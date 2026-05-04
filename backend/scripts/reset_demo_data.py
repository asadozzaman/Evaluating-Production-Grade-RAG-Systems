from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from sqlalchemy import select, text
from sqlalchemy.orm import Session

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.config import get_settings
from app.database import SessionLocal
from app.models import (
    AuditEvent,
    BackgroundJob,
    DocumentChunk,
    ErrorAnnotation,
    EvaluationRecord,
    EvaluationRun,
    GeneratedAnswer,
    Project,
    QuestionDataset,
    RetrievedChunk,
    Role,
    SourceDocument,
    TestQuestion,
    User,
)
from app.security import hash_password


SAMPLE_POLICY_TEXT = """HR Leave Policy

Section 1.1 Annual Leave
Full-time employees receive 20 annual leave days after one year of continuous service.

Section 1.2 Sick Leave
Employees must provide a medical certificate after three consecutive sick days.

Section 1.3 Carry Forward
Employees may carry forward up to 5 unused annual leave days with manager approval.

Section 1.4 Probation
Employees in probation accrue leave monthly, but annual leave normally becomes available after confirmation.
"""


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def json_default(value: object) -> str:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def dump_json(payload: dict[str, object]) -> str:
    return json.dumps(payload, default=json_default, sort_keys=True)


def ensure_roles(db: Session) -> dict[str, Role]:
    role_specs = {
        "admin": "Admin role",
        "evaluator": "Evaluator role",
        "viewer": "Viewer role",
    }
    roles: dict[str, Role] = {}
    for name, description in role_specs.items():
        role = db.scalar(select(Role).where(Role.name == name))
        if role is None:
            role = Role(name=name, description=description)
            db.add(role)
            db.flush()
        roles[name] = role
    return roles


def ensure_user(db: Session, roles: dict[str, Role], email: str, full_name: str, password: str, role_name: str) -> User:
    user = db.scalar(select(User).where(User.email == email.lower()))
    if user is None:
        user = User(
            email=email.lower(),
            full_name=full_name,
            hashed_password=hash_password(password),
            roles=[roles[role_name]],
        )
        db.add(user)
        db.flush()
    return user


def clean_project_data(db: Session) -> None:
    table_names = [
        "background_jobs",
        "audit_events",
        "error_annotations",
        "evaluation_records",
        "retrieved_chunks",
        "generated_answers",
        "document_chunks",
        "evaluation_runs",
        "test_questions",
        "question_datasets",
        "source_documents",
        "projects",
    ]
    if db.bind is not None and db.bind.dialect.name == "postgresql":
        db.execute(text(f"TRUNCATE TABLE {', '.join(table_names)} RESTART IDENTITY CASCADE"))
    else:
        for table_name in table_names:
            db.execute(text(f"DELETE FROM {table_name}"))


def clean_uploads() -> None:
    settings = get_settings()
    upload_root = Path(settings.upload_dir)
    if not upload_root.is_absolute():
        upload_root = BACKEND_ROOT / upload_root
    documents_root = upload_root / "documents"
    if documents_root.exists():
        shutil.rmtree(documents_root)


def audit(
    db: Session,
    actor: User,
    *,
    event_type: str,
    entity_type: str,
    entity_id: int | None,
    summary: str,
    project_id: int | None = None,
    run_id: int | None = None,
    question_id: int | None = None,
    answer_id: int | None = None,
    evaluation_id: int | None = None,
    metadata: dict[str, object] | None = None,
) -> None:
    db.add(
        AuditEvent(
            actor_user_id=actor.id,
            project_id=project_id,
            evaluation_run_id=run_id,
            test_question_id=question_id,
            generated_answer_id=answer_id,
            evaluation_record_id=evaluation_id,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            event_summary=summary,
            metadata_json=dump_json(metadata) if metadata else None,
        )
    )


def create_demo_data(db: Session, admin: User, viewer: User) -> dict[str, int]:
    project = Project(
        name="HR Policy RAG Assistant",
        description="Clean demo project for evaluating a production-grade RAG assistant using the CLEAR-RAG framework.",
        system_type="hr_policy_rag",
        target_users="Employees and HR operations team",
        created_by_user_id=admin.id,
    )
    db.add(project)
    db.flush()
    audit(
        db,
        admin,
        event_type="project_created",
        entity_type="project",
        entity_id=project.id,
        project_id=project.id,
        summary="Demo project was created.",
    )

    upload_root = Path(get_settings().upload_dir)
    if not upload_root.is_absolute():
        upload_root = BACKEND_ROOT / upload_root
    relative_path = Path("documents") / str(project.id) / "hr-leave-policy-demo.txt"
    absolute_path = upload_root / relative_path
    absolute_path.parent.mkdir(parents=True, exist_ok=True)
    absolute_path.write_text(SAMPLE_POLICY_TEXT, encoding="utf-8")

    document = SourceDocument(
        project_id=project.id,
        title="HR Leave Policy",
        document_type="policy",
        source_kind="file",
        version="v1",
        original_file_name="HR Leave Policy.txt",
        stored_file_name="hr-leave-policy-demo.txt",
        content_type="text/plain",
        file_size_bytes=absolute_path.stat().st_size,
        storage_path=str(relative_path).replace("\\", "/"),
    )
    db.add(document)
    db.flush()
    audit(
        db,
        admin,
        event_type="document_uploaded",
        entity_type="source_document",
        entity_id=document.id,
        project_id=project.id,
        summary="Sample HR Leave Policy file was uploaded.",
        metadata={"original_file_name": document.original_file_name},
    )

    chunk_texts = [
        ("Section 1.1", "Full-time employees receive 20 annual leave days after one year of continuous service."),
        ("Section 1.2", "Employees must provide a medical certificate after three consecutive sick days."),
        ("Section 1.3", "Employees may carry forward up to 5 unused annual leave days with manager approval."),
        ("Section 1.4", "Employees in probation accrue leave monthly, but annual leave normally becomes available after confirmation."),
    ]
    document_chunks: list[DocumentChunk] = []
    for index, (section, text_value) in enumerate(chunk_texts, start=1):
        chunk = DocumentChunk(
            source_document_id=document.id,
            chunk_index=index,
            chunk_text=text_value,
            section_reference=section,
            embedding_model="demo-keyword-vector",
            embedding_json=json.dumps([round(index * 0.1, 2), round(index * 0.2, 2), round(index * 0.3, 2)]),
        )
        db.add(chunk)
        document_chunks.append(chunk)

    dataset = QuestionDataset(
        project_id=project.id,
        dataset_name="HR Policy Regression Set",
        dataset_version="v1",
        imported_file_name="hr-policy-regression.csv",
        question_count=4,
        created_by_user_id=admin.id,
    )
    db.add(dataset)
    db.flush()
    audit(
        db,
        admin,
        event_type="question_dataset_imported",
        entity_type="question_dataset",
        entity_id=dataset.id,
        project_id=project.id,
        summary="Sample HR regression question set was imported.",
        metadata={"question_count": dataset.question_count},
    )

    question_specs = [
        (
            "How many annual leave days does an employee receive after one year?",
            "simple_factual",
            "HR Leave Policy, Section 1.1",
        ),
        (
            "When is a medical certificate required for sick leave?",
            "conditional",
            "HR Leave Policy, Section 1.2",
        ),
        (
            "How many unused annual leave days can be carried forward?",
            "simple_factual",
            "HR Leave Policy, Section 1.3",
        ),
        (
            "Can a probation employee use annual leave immediately?",
            "edge_case",
            "HR Leave Policy, Section 1.4",
        ),
    ]
    questions: list[TestQuestion] = []
    for text_value, question_type, expected_source in question_specs:
        question = TestQuestion(
            project_id=project.id,
            question_text=text_value,
            question_type=question_type,
            expected_source=expected_source,
            dataset_id=dataset.id,
            created_by_user_id=admin.id,
        )
        db.add(question)
        db.flush()
        questions.append(question)
        audit(
            db,
            admin,
            event_type="question_created",
            entity_type="test_question",
            entity_id=question.id,
            project_id=project.id,
            question_id=question.id,
            summary="Sample test question was added.",
            metadata={"question_type": question.question_type},
        )

    run = EvaluationRun(
        project_id=project.id,
        name="Baseline Evaluation",
        system_version="demo-v1",
        notes="Clean seeded run with sample retrieved chunks, answers, human review, error taxonomy, readiness, and report data.",
        status="completed",
        processed_question_count=len(questions),
        dataset_id=dataset.id,
        batch_document_ids=json.dumps([document.id]),
        auto_evaluate_enabled=True,
        batch_status="completed",
        current_step="completed",
        completed_steps=json.dumps(["rag_execution", "automated_evaluation", "human_review", "report_builder"]),
        retrieval_mode="keyword",
        generator_model_name="gemini-2.5-flash",
        embedding_model_name="demo-keyword-vector",
        judge_model_name="gemini-2.5-flash",
        created_by_user_id=admin.id,
        batch_started_at=utcnow(),
        batch_completed_at=utcnow(),
    )
    db.add(run)
    db.flush()
    audit(
        db,
        admin,
        event_type="run_created",
        entity_type="evaluation_run",
        entity_id=run.id,
        project_id=project.id,
        run_id=run.id,
        summary="Baseline Evaluation run was created.",
    )

    answer_texts = [
        "Employees receive 20 annual leave days after one year of continuous service. Source: HR Leave Policy Section 1.1.",
        "A medical certificate is required after three consecutive sick days. Source: HR Leave Policy Section 1.2.",
        "Employees may carry forward up to 5 unused annual leave days with manager approval. Source: HR Leave Policy Section 1.3.",
        "Probation employees accrue leave monthly, but annual leave normally becomes available after confirmation. Source: HR Leave Policy Section 1.4.",
    ]
    score_specs = [
        (5, 4, 5, 5, 5),
        (5, 4, 5, 5, 4),
        (4, 4, 5, 5, 5),
        (3, 4, 4, 4, 4),
    ]
    answers: list[GeneratedAnswer] = []
    evaluations: list[EvaluationRecord] = []
    for index, question in enumerate(questions):
        chunk = RetrievedChunk(
            evaluation_run_id=run.id,
            test_question_id=question.id,
            source_document_id=document.id,
            rank=1,
            chunk_text=chunk_texts[index][1],
            section_reference=chunk_texts[index][0],
            relevance_label="high",
            retrieval_time_ms=85 + index * 10,
        )
        db.add(chunk)

        answer = GeneratedAnswer(
            evaluation_run_id=run.id,
            test_question_id=question.id,
            answer_text=answer_texts[index],
            model_name="gemini-2.5-flash",
            input_tokens=120 + index * 8,
            output_tokens=35 + index * 4,
            generation_time_ms=900 + index * 80,
            estimated_cost=Decimal("0.002500") + Decimal(index) * Decimal("0.000100"),
        )
        db.add(answer)
        db.flush()
        answers.append(answer)
        audit(
            db,
            admin,
            event_type="generated_answer_added",
            entity_type="generated_answer",
            entity_id=answer.id,
            project_id=project.id,
            run_id=run.id,
            question_id=question.id,
            answer_id=answer.id,
            summary="Sample generated answer was added.",
            metadata={"model_name": answer.model_name},
        )

        citation, latency, faithfulness, relevance, retrieval = score_specs[index]
        overall = (Decimal(citation + latency + faithfulness + relevance + retrieval) / Decimal("5")).quantize(Decimal("0.01"))
        evaluation = EvaluationRecord(
            evaluation_run_id=run.id,
            test_question_id=question.id,
            generated_answer_id=answer.id,
            reviewer_user_id=admin.id,
            citation_quality_score=citation,
            latency_cost_score=latency,
            evidence_faithfulness_score=faithfulness,
            answer_relevance_score=relevance,
            retrieval_quality_score=retrieval,
            overall_score=overall,
            reviewer_notes="Seeded human review confirms the answer is grounded in the supplied policy.",
            suggested_improvement="Keep citations tied to exact policy sections.",
            evaluation_mode="human",
            review_status="approved" if index < 3 else "needs_revision",
            reviewed_by_user_id=admin.id,
            reviewed_at=utcnow(),
            review_notes="Approved sample review." if index < 3 else "Needs a clearer probation caveat.",
            score_change_reason=None,
        )
        db.add(evaluation)
        db.flush()
        evaluations.append(evaluation)
        audit(
            db,
            admin,
            event_type="human_evaluation_created",
            entity_type="evaluation_record",
            entity_id=evaluation.id,
            project_id=project.id,
            run_id=run.id,
            question_id=question.id,
            answer_id=answer.id,
            evaluation_id=evaluation.id,
            summary="Sample human evaluation was recorded.",
            metadata={"overall_score": evaluation.overall_score, "review_status": evaluation.review_status},
        )

    annotation = ErrorAnnotation(
        evaluation_run_id=run.id,
        test_question_id=questions[3].id,
        generated_answer_id=answers[3].id,
        evaluation_record_id=evaluations[3].id,
        created_by_user_id=admin.id,
        category="policy_ambiguity",
        severity="medium",
        source="human",
        notes="Probation leave rules need a clearer qualification for employee-facing answers.",
        evidence_reference="HR Leave Policy, Section 1.4",
    )
    db.add(annotation)
    db.flush()
    audit(
        db,
        admin,
        event_type="error_tag_created",
        entity_type="error_annotation",
        entity_id=annotation.id,
        project_id=project.id,
        run_id=run.id,
        question_id=annotation.test_question_id,
        answer_id=annotation.generated_answer_id,
        evaluation_id=annotation.evaluation_record_id,
        summary="Sample policy ambiguity error tag was added.",
        metadata={"category": annotation.category, "severity": annotation.severity},
    )

    report_markdown = """# HR Policy RAG Assistant Demo Report

## Overview
Baseline Evaluation contains 4 test questions, 4 generated answers, and 4 human reviews.

## Production Readiness
The demo run is useful for testing but has one medium policy ambiguity item to inspect.

## Question Results
- Annual leave: correct answer with Section 1.1 citation.
- Sick leave: correct answer with Section 1.2 citation.
- Carry forward: correct answer with Section 1.3 citation.
- Probation leave: answer needs a clearer caveat.
"""
    job = BackgroundJob(
        job_type="report_builder",
        status="completed",
        project_id=project.id,
        evaluation_run_id=run.id,
        requested_by_user_id=viewer.id,
        current_step="completed",
        input_json=dump_json({"title": "HR Policy Demo Report", "audience": "technical"}),
        result_json=dump_json({"title": "HR Policy Demo Report", "markdown": report_markdown}),
        created_at=utcnow(),
        started_at=utcnow(),
        completed_at=utcnow(),
    )
    db.add(job)
    db.flush()
    audit(
        db,
        viewer,
        event_type="background_job_completed",
        entity_type="background_job",
        entity_id=job.id,
        project_id=project.id,
        run_id=run.id,
        summary="Sample report background job completed.",
        metadata={"job_type": job.job_type},
    )
    audit(
        db,
        viewer,
        event_type="report_built",
        entity_type="report",
        entity_id=run.id,
        project_id=project.id,
        run_id=run.id,
        summary="Sample HR Policy Demo Report was generated.",
        metadata={"audience": "technical", "sections": ["overview", "readiness", "questions"]},
    )

    return {
        "project_id": project.id,
        "document_id": document.id,
        "dataset_id": dataset.id,
        "run_id": run.id,
        "question_count": len(questions),
        "answer_count": len(answers),
        "evaluation_count": len(evaluations),
        "background_job_id": job.id,
    }


def main() -> None:
    with SessionLocal() as db:
        roles = ensure_roles(db)
        admin = ensure_user(db, roles, "admin@clearrag.com", "CLEAR-RAG Admin", "AdminPass123!", "admin")
        viewer = ensure_user(db, roles, "viewer@clearrag.com", "CLEAR-RAG Viewer", "ViewerPass123!", "viewer")
        clean_project_data(db)
        clean_uploads()
        summary = create_demo_data(db, admin, viewer)
        db.commit()
        print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
