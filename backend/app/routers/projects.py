import re
import csv
import io
import json
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Query, Response, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_roles
from app.config import BACKEND_ROOT, get_settings
from app.database import SessionLocal, get_db
from app.models import AuditEvent, BackgroundJob, DocumentChunk, ErrorAnnotation, EvaluationRecord, EvaluationRun, Project, QuestionDataset, SourceDocument, TestQuestion, User
from app.models import GeneratedAnswer, RetrievedChunk
from app.schemas import (
    AuditEventRead,
    AutoEvaluationRunRead,
    BackgroundJobRead,
    BatchExperimentCreate,
    BatchExperimentRead,
    DocumentChunkRead,
    DocumentIndexRead,
    ErrorAnnotationCreate,
    ErrorAnnotationRead,
    ErrorAnnotationUpdate,
    ErrorTaxonomyRead,
    ExperimentLeaderboardRead,
    EvaluationRecordCreate,
    EvaluationRecordRead,
    EvaluationRecordUpdate,
    EvaluationReviewUpdate,
    EvaluationRunCreate,
    EvaluationRunRead,
    EvaluationRunUpdate,
    GeneratedAnswerCreate,
    GeneratedAnswerRead,
    GovernanceSummaryRead,
    JudgeCalibrationRead,
    ProjectCreate,
    ProjectRead,
    ProjectUpdate,
    ProjectSummaryRead,
    ProductionReadinessRead,
    QuestionDatasetRead,
    QuestionImportRead,
    RagExecutionRequest,
    RagExecutionRead,
    ReportBuilderRead,
    ReportBuilderRequest,
    RetrievalMetricsRead,
    RunComparisonRead,
    RunReviewDashboardRead,
    RetrievedChunkCreate,
    RetrievedChunkRead,
    RunSummaryRead,
    SourceDocumentCreate,
    SourceDocumentRead,
    SourceDocumentUpdate,
    TestQuestionCreate,
    TestQuestionRead,
    TestQuestionUpdate,
)
from app.services.clear_rag_judge import judge_clear_rag_answer
from app.services.gemini import GeminiClient
from app.services.rag_execution import RagExecutionError, execute_rag_run
from app.services.vector_index import index_source_document


router = APIRouter(prefix="/projects", tags=["projects"])

WritableUser = Annotated[User, Depends(require_roles(["admin", "evaluator"]))]
AuthenticatedUser = Annotated[User, Depends(get_current_user)]
ALLOWED_UPLOAD_EXTENSIONS = {".pdf", ".docx", ".txt", ".csv", ".md"}
ALLOWED_QUESTION_IMPORT_EXTENSIONS = {".csv", ".json"}
QUESTION_TYPES = {"simple_factual", "conditional", "multi_document", "ambiguous", "edge_case"}
QUESTION_IMPORT_REQUIRED_COLUMNS = {"question_text", "question_type"}
RETRIEVAL_METRIC_K = 3
SCORE_FIELDS = [
    "citation_quality_score",
    "latency_cost_score",
    "evidence_faithfulness_score",
    "answer_relevance_score",
    "retrieval_quality_score",
]
DIMENSION_LABELS = {
    "citation_quality_score": "Citation Quality",
    "latency_cost_score": "Latency and Cost Efficiency",
    "evidence_faithfulness_score": "Evidence Faithfulness",
    "answer_relevance_score": "Answer Relevance",
    "retrieval_quality_score": "Retrieval Quality",
}
ERROR_CATEGORY_LABELS = {
    "retrieval_miss": "Retrieval Miss",
    "citation_error": "Citation Error",
    "hallucination": "Hallucination",
    "incomplete_answer": "Incomplete Answer",
    "irrelevant_answer": "Irrelevant Answer",
    "contradiction": "Contradiction",
    "latency_cost": "Latency or Cost",
    "format_error": "Format Error",
    "policy_ambiguity": "Policy Ambiguity",
    "other": "Other",
}
ERROR_SEVERITY_LABELS = {
    "low": "Low",
    "medium": "Medium",
    "high": "High",
    "critical": "Critical",
}
MIN_PRODUCTION_SCORE = Decimal("4.00")
MIN_RETRIEVAL_HIT_RATE = Decimal("0.80")
MIN_JUDGE_WITHIN_ONE_AGREEMENT = Decimal("80.00")


def json_audit_default(value: object) -> str:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def create_audit_event(
    db: Session,
    actor: User | None,
    *,
    event_type: str,
    entity_type: str,
    entity_id: int | None,
    event_summary: str,
    project_id: int | None = None,
    run_id: int | None = None,
    question_id: int | None = None,
    answer_id: int | None = None,
    evaluation_record_id: int | None = None,
    metadata: dict[str, object] | None = None,
) -> AuditEvent:
    event = AuditEvent(
        actor_user_id=actor.id if actor is not None else None,
        project_id=project_id,
        evaluation_run_id=run_id,
        test_question_id=question_id,
        generated_answer_id=answer_id,
        evaluation_record_id=evaluation_record_id,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        event_summary=event_summary,
        metadata_json=json.dumps(metadata, default=json_audit_default, sort_keys=True) if metadata else None,
    )
    db.add(event)
    return event


def create_background_job(
    db: Session,
    current_user: User,
    *,
    job_type: str,
    project_id: int,
    run_id: int | None = None,
    current_step: str | None = "queued",
    input_payload: dict[str, object] | None = None,
) -> BackgroundJob:
    job = BackgroundJob(
        job_type=job_type,
        status="queued",
        project_id=project_id,
        evaluation_run_id=run_id,
        requested_by_user_id=current_user.id,
        current_step=current_step,
        input_json=json.dumps(input_payload, default=json_audit_default, sort_keys=True) if input_payload else None,
    )
    db.add(job)
    db.flush()
    create_audit_event(
        db,
        current_user,
        event_type="background_job_queued",
        entity_type="background_job",
        entity_id=job.id,
        project_id=project_id,
        run_id=run_id,
        event_summary=f"Background job '{job_type}' was queued.",
        metadata={"job_type": job_type, "input": input_payload or {}},
    )
    return job


def get_background_job_or_404(db: Session, project_id: int, job_id: int) -> BackgroundJob:
    job = db.get(BackgroundJob, job_id)
    if job is None or job.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Background job not found")
    return job


def load_job_input(job: BackgroundJob) -> dict[str, object]:
    if not job.input_json:
        return {}
    try:
        payload = json.loads(job.input_json)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def serialize_job_result(payload: dict[str, object]) -> str:
    return json.dumps(payload, default=json_audit_default, sort_keys=True)


def process_background_job(job_id: int) -> None:
    db = SessionLocal()
    try:
        job = db.get(BackgroundJob, job_id)
        if job is None:
            return

        actor = db.get(User, job.requested_by_user_id)
        project = get_project_or_404(db, job.project_id)
        run = get_run_or_404(db, job.project_id, job.evaluation_run_id) if job.evaluation_run_id is not None else None

        job.status = "running"
        job.current_step = "running"
        job.started_at = datetime.now(timezone.utc)
        db.commit()

        input_payload = load_job_input(job)
        result: dict[str, object]
        if job.job_type == "rag_execution":
            if run is None:
                raise ValueError("RAG execution jobs require an evaluation run.")
            retrieval_mode = str(input_payload.get("retrieval_mode") or "keyword")
            job.current_step = "executing_rag"
            db.commit()
            rag_result = execute_rag_run(db, run, get_settings(), retrieval_mode=retrieval_mode)
            result = {
                "run_id": rag_result.run_id,
                "status": rag_result.status,
                "model_name": rag_result.model_name,
                "processed_questions": rag_result.processed_questions,
                "retrieved_chunks_created": rag_result.retrieved_chunks_created,
                "generated_answers_created": rag_result.generated_answers_created,
                "retrieval_mode": rag_result.retrieval_mode,
                "message": rag_result.message,
            }
            if actor is not None:
                create_audit_event(
                    db,
                    actor,
                    event_type="rag_executed",
                    entity_type="evaluation_run",
                    entity_id=run.id,
                    project_id=job.project_id,
                    run_id=run.id,
                    event_summary=f"Gemini RAG was executed by background job for run '{run.name}'.",
                    metadata=result,
                )
        elif job.job_type == "automated_evaluation":
            if run is None or actor is None:
                raise ValueError("Automated evaluation jobs require an evaluation run and actor.")
            job.current_step = "running_clear_rag_judge"
            db.commit()
            result = run_automated_clear_rag_evaluation(db, job.project_id, run, actor)
        elif job.job_type == "report_builder":
            if run is None or actor is None:
                raise ValueError("Report builder jobs require an evaluation run and actor.")
            job.current_step = "building_report"
            db.commit()
            report_payload = ReportBuilderRequest(**input_payload)
            result = build_run_report(db, project, run, report_payload)
            create_audit_event(
                db,
                actor,
                event_type="report_built",
                entity_type="report",
                entity_id=run.id,
                project_id=job.project_id,
                run_id=run.id,
                event_summary=f"Report '{result['title']}' was generated by background job for run '{run.name}'.",
                metadata={"audience": report_payload.audience, "sections": report_payload.sections},
            )
        else:
            raise ValueError(f"Unsupported background job type: {job.job_type}")

        job.status = "completed"
        job.current_step = "completed"
        job.result_json = serialize_job_result(result)
        job.error_message = None
        job.completed_at = datetime.now(timezone.utc)
        if actor is not None:
            create_audit_event(
                db,
                actor,
                event_type="background_job_completed",
                entity_type="background_job",
                entity_id=job.id,
                project_id=job.project_id,
                run_id=job.evaluation_run_id,
                event_summary=f"Background job '{job.job_type}' completed.",
                metadata={"job_type": job.job_type},
            )
        db.commit()
    except Exception as exc:
        db.rollback()
        failed_job = db.get(BackgroundJob, job_id)
        if failed_job is not None:
            failed_job.status = "failed"
            failed_job.current_step = "failed"
            failed_job.error_message = str(exc)
            failed_job.completed_at = datetime.now(timezone.utc)
            actor = db.get(User, failed_job.requested_by_user_id)
            if actor is not None:
                create_audit_event(
                    db,
                    actor,
                    event_type="background_job_failed",
                    entity_type="background_job",
                    entity_id=failed_job.id,
                    project_id=failed_job.project_id,
                    run_id=failed_job.evaluation_run_id,
                    event_summary=f"Background job '{failed_job.job_type}' failed.",
                    metadata={"error": str(exc)},
                )
            db.commit()
    finally:
        db.close()


def audit_bucket_counts(events: list[AuditEvent], field_name: str) -> list[dict[str, object]]:
    counts: dict[str, int] = {}
    for event in events:
        key = getattr(event, field_name)
        counts[key] = counts.get(key, 0) + 1
    return [
        {"key": key, "count": count}
        for key, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    ]


def build_governance_summary(db: Session, project: Project) -> dict[str, object]:
    events = list(
        db.scalars(
            select(AuditEvent)
            .where(AuditEvent.project_id == project.id)
            .order_by(AuditEvent.created_at.desc(), AuditEvent.id.desc())
        ).all()
    )
    actor_ids = {event.actor_user_id for event in events if event.actor_user_id is not None}
    return {
        "project_id": project.id,
        "project_name": project.name,
        "total_events": len(events),
        "active_actor_count": len(actor_ids),
        "run_event_count": sum(1 for event in events if event.evaluation_run_id is not None),
        "event_type_counts": audit_bucket_counts(events, "event_type"),
        "entity_type_counts": audit_bucket_counts(events, "entity_type"),
        "recent_events": events[:20],
    }


def get_project_or_404(db: Session, project_id: int) -> Project:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


def get_document_or_404(db: Session, project_id: int, document_id: int) -> SourceDocument:
    document = db.scalar(
        select(SourceDocument).where(
            SourceDocument.id == document_id,
            SourceDocument.project_id == project_id,
        )
    )
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source document not found")
    return document


def get_dataset_or_404(db: Session, project_id: int, dataset_id: int) -> QuestionDataset:
    dataset = db.scalar(
        select(QuestionDataset).where(
            QuestionDataset.id == dataset_id,
            QuestionDataset.project_id == project_id,
        )
    )
    if dataset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question dataset not found")
    return dataset


def get_documents_or_404(db: Session, project_id: int, document_ids: list[int]) -> list[SourceDocument]:
    unique_document_ids = list(dict.fromkeys(document_ids))
    documents = list(
        db.scalars(
            select(SourceDocument)
            .where(
                SourceDocument.project_id == project_id,
                SourceDocument.id.in_(unique_document_ids),
            )
            .order_by(SourceDocument.created_at.asc(), SourceDocument.id.asc())
        ).all()
    )
    found_document_ids = {document.id for document in documents}
    missing_document_ids = [document_id for document_id in unique_document_ids if document_id not in found_document_ids]
    if missing_document_ids:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="One or more source documents were not found in this project.")
    return documents


def get_question_or_404(db: Session, project_id: int, question_id: int) -> TestQuestion:
    question = db.scalar(
        select(TestQuestion).where(
            TestQuestion.id == question_id,
            TestQuestion.project_id == project_id,
        )
    )
    if question is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test question not found")
    return question


def get_run_or_404(db: Session, project_id: int, run_id: int) -> EvaluationRun:
    run = db.scalar(
        select(EvaluationRun).where(
            EvaluationRun.id == run_id,
            EvaluationRun.project_id == project_id,
        )
    )
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation run not found")
    return run


def get_chunk_or_404(db: Session, run_id: int, question_id: int, chunk_id: int) -> RetrievedChunk:
    chunk = db.scalar(
        select(RetrievedChunk).where(
            RetrievedChunk.id == chunk_id,
            RetrievedChunk.evaluation_run_id == run_id,
            RetrievedChunk.test_question_id == question_id,
        )
    )
    if chunk is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Retrieved chunk not found")
    return chunk


def get_answer_or_404(db: Session, run_id: int, question_id: int, answer_id: int) -> GeneratedAnswer:
    answer = db.scalar(
        select(GeneratedAnswer).where(
            GeneratedAnswer.id == answer_id,
            GeneratedAnswer.evaluation_run_id == run_id,
            GeneratedAnswer.test_question_id == question_id,
        )
    )
    if answer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Generated answer not found")
    return answer


def get_evaluation_or_404(db: Session, run_id: int, evaluation_id: int) -> EvaluationRecord:
    evaluation = db.scalar(
        select(EvaluationRecord).where(
            EvaluationRecord.id == evaluation_id,
            EvaluationRecord.evaluation_run_id == run_id,
        )
    )
    if evaluation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation record not found")
    return evaluation


def get_error_annotation_or_404(db: Session, run_id: int, error_id: int) -> ErrorAnnotation:
    annotation = db.scalar(
        select(ErrorAnnotation).where(
            ErrorAnnotation.id == error_id,
            ErrorAnnotation.evaluation_run_id == run_id,
        )
    )
    if annotation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Error annotation not found")
    return annotation


def validate_output_scope(
    db: Session,
    project_id: int,
    run_id: int,
    question_id: int,
    source_document_id: int | None = None,
) -> tuple[EvaluationRun, TestQuestion, SourceDocument | None]:
    run = get_run_or_404(db, project_id, run_id)
    question = get_question_or_404(db, project_id, question_id)
    document = None
    if source_document_id is not None:
        document = get_document_or_404(db, project_id, source_document_id)
    return run, question, document


def validate_error_evaluation_scope(
    db: Session,
    run_id: int,
    question_id: int,
    answer_id: int,
    evaluation_record_id: int | None,
) -> EvaluationRecord | None:
    if evaluation_record_id is None:
        return None
    evaluation = get_evaluation_or_404(db, run_id, evaluation_record_id)
    if evaluation.test_question_id != question_id or evaluation.generated_answer_id != answer_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Evaluation record must belong to the selected question and answer.",
        )
    return evaluation


def calculate_overall_score(record: object) -> Decimal:
    scores = [
        Decimal(getattr(record, "citation_quality_score")),
        Decimal(getattr(record, "latency_cost_score")),
        Decimal(getattr(record, "evidence_faithfulness_score")),
        Decimal(getattr(record, "answer_relevance_score")),
        Decimal(getattr(record, "retrieval_quality_score")),
    ]
    return (sum(scores) / Decimal(len(scores))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def decimal_average(values: list[Decimal]) -> Decimal | None:
    if not values:
        return None
    return (sum(values) / Decimal(len(values))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def percent(part: int, whole: int) -> Decimal:
    if whole == 0:
        return Decimal("0.00")
    return (Decimal(part) * Decimal("100") / Decimal(whole)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def decimal_ratio(part: int, whole: int) -> Decimal | None:
    if whole == 0:
        return None
    return (Decimal(part) / Decimal(whole)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def latest_by_id(items: list[object]) -> object | None:
    if not items:
        return None
    return sorted(items, key=lambda item: getattr(item, "id"), reverse=True)[0]


def set_batch_step(run: EvaluationRun, current_step: str, completed_step: str | None = None) -> None:
    completed_steps = json.loads(run.completed_steps or "[]")
    if completed_step and completed_step not in completed_steps:
        completed_steps.append(completed_step)
    run.current_step = current_step
    run.completed_steps = json.dumps(completed_steps)


def normalize_metric_text(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", value.lower())).strip()


def expected_source_matches(question: TestQuestion, chunk: RetrievedChunk, source_document: SourceDocument | None) -> bool:
    expected_source = normalize_metric_text(question.expected_source)
    if not expected_source:
        return False
    haystack = normalize_metric_text(
        " ".join(
            [
                source_document.title if source_document else "",
                source_document.source_uri if source_document and source_document.source_uri else "",
                chunk.section_reference or "",
                chunk.chunk_text,
            ]
        )
    )
    if expected_source in haystack:
        return True
    expected_terms = [term for term in expected_source.split() if len(term) > 2]
    if not expected_terms:
        return False
    matched_terms = sum(1 for term in expected_terms if term in haystack)
    return Decimal(matched_terms) / Decimal(len(expected_terms)) >= Decimal("0.60")


def build_retrieval_metrics(
    project: Project,
    run: EvaluationRun,
    questions: list[TestQuestion],
    chunks: list[RetrievedChunk],
    source_documents: dict[int, SourceDocument],
) -> dict[str, object]:
    chunks_by_question: dict[int, list[RetrievedChunk]] = {}
    for chunk in chunks:
        chunks_by_question.setdefault(chunk.test_question_id, []).append(chunk)

    question_metrics = []
    precision_values: list[Decimal] = []
    recall_values: list[Decimal] = []
    reciprocal_rank_values: list[Decimal] = []
    questions_with_expected_source = 0
    expected_source_hit_count = 0
    questions_with_retrieved_chunks = 0
    missing_evidence_count = 0

    for question in questions:
        question_chunks = sorted(chunks_by_question.get(question.id, []), key=lambda chunk: (chunk.rank, chunk.id))
        top_chunks = question_chunks[:RETRIEVAL_METRIC_K]
        expected_source_available = bool(normalize_metric_text(question.expected_source))
        if expected_source_available:
            questions_with_expected_source += 1
        if question_chunks:
            questions_with_retrieved_chunks += 1

        relevant_chunks = [
            chunk
            for chunk in top_chunks
            if expected_source_matches(question, chunk, source_documents.get(chunk.source_document_id))
        ]
        first_relevant_rank = relevant_chunks[0].rank if relevant_chunks else None
        expected_source_match = None
        precision_at_k = None
        recall_at_k = None
        reciprocal_rank = None
        missing_evidence = False
        if expected_source_available:
            expected_source_match = first_relevant_rank is not None
            precision_at_k = decimal_ratio(len(relevant_chunks), len(top_chunks)) if top_chunks else Decimal("0.00")
            recall_at_k = Decimal("1.00") if expected_source_match else Decimal("0.00")
            reciprocal_rank = (Decimal("1") / Decimal(first_relevant_rank)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if first_relevant_rank else Decimal("0.00")
            precision_values.append(precision_at_k)
            recall_values.append(recall_at_k)
            reciprocal_rank_values.append(reciprocal_rank)
            if expected_source_match:
                expected_source_hit_count += 1
            else:
                missing_evidence = True
                missing_evidence_count += 1

        question_metrics.append(
            {
                "question_id": question.id,
                "question_text": question.question_text,
                "expected_source": question.expected_source,
                "expected_source_available": expected_source_available,
                "retrieved_chunk_count": len(question_chunks),
                "relevant_chunk_count": len(relevant_chunks),
                "expected_source_match": expected_source_match,
                "first_relevant_rank": first_relevant_rank,
                "precision_at_k": precision_at_k,
                "recall_at_k": recall_at_k,
                "reciprocal_rank": reciprocal_rank,
                "missing_evidence": missing_evidence,
            }
        )

    return {
        "project_id": project.id,
        "run_id": run.id,
        "evaluated_question_count": len(questions),
        "questions_with_expected_source": questions_with_expected_source,
        "questions_with_retrieved_chunks": questions_with_retrieved_chunks,
        "expected_source_hit_count": expected_source_hit_count,
        "missing_evidence_count": missing_evidence_count,
        "hit_rate": decimal_ratio(expected_source_hit_count, questions_with_expected_source),
        "precision_at_k": decimal_average(precision_values),
        "recall_at_k": decimal_average(recall_values),
        "mean_reciprocal_rank": decimal_average(reciprocal_rank_values),
        "chunk_coverage": decimal_ratio(questions_with_retrieved_chunks, len(questions)),
        "question_metrics": question_metrics,
    }


def build_run_summary(db: Session, project: Project, run: EvaluationRun) -> dict[str, object]:
    question_statement = select(TestQuestion).where(TestQuestion.project_id == project.id)
    if run.dataset_id is not None:
        question_statement = question_statement.where(TestQuestion.dataset_id == run.dataset_id)
    questions = list(
        db.scalars(
            question_statement.order_by(TestQuestion.created_at.asc(), TestQuestion.id.asc())
        ).all()
    )
    answers = list(
        db.scalars(
            select(GeneratedAnswer)
            .where(GeneratedAnswer.evaluation_run_id == run.id)
            .order_by(GeneratedAnswer.created_at.asc(), GeneratedAnswer.id.asc())
        ).all()
    )
    evaluations = list(
        db.scalars(
            select(EvaluationRecord)
            .where(EvaluationRecord.evaluation_run_id == run.id)
            .order_by(EvaluationRecord.created_at.asc(), EvaluationRecord.id.asc())
        ).all()
    )
    retrieved_chunks = list(
        db.scalars(
            select(RetrievedChunk)
            .where(RetrievedChunk.evaluation_run_id == run.id)
            .order_by(RetrievedChunk.test_question_id.asc(), RetrievedChunk.rank.asc(), RetrievedChunk.id.asc())
        ).all()
    )
    source_documents = {
        document.id: document
        for document in db.scalars(select(SourceDocument).where(SourceDocument.project_id == project.id)).all()
    }
    retrieval_metrics = build_retrieval_metrics(project, run, questions, retrieved_chunks, source_documents)
    retrieval_metrics_by_question = {
        metric["question_id"]: metric for metric in retrieval_metrics["question_metrics"]
    }

    answers_by_question: dict[int, list[GeneratedAnswer]] = {}
    for answer in answers:
        answers_by_question.setdefault(answer.test_question_id, []).append(answer)

    evaluations_by_answer: dict[int, list[EvaluationRecord]] = {}
    for evaluation in evaluations:
        evaluations_by_answer.setdefault(evaluation.generated_answer_id, []).append(evaluation)

    dimension_averages = {
        field: decimal_average([Decimal(getattr(evaluation, field)) for evaluation in evaluations])
        for field in SCORE_FIELDS
    }
    available_dimensions = {field: value for field, value in dimension_averages.items() if value is not None}
    weakest_dimension = None
    if available_dimensions:
        weakest_field = min(available_dimensions, key=lambda field: available_dimensions[field] or Decimal("0"))
        weakest_dimension = DIMENSION_LABELS[weakest_field]

    reviewed_answer_ids = set(evaluations_by_answer)
    question_results = []
    for question in questions:
        question_answers = answers_by_question.get(question.id, [])
        latest_answer = latest_by_id(question_answers)
        latest_evaluation = None
        if latest_answer is not None:
            latest_evaluation = latest_by_id(evaluations_by_answer.get(latest_answer.id, []))
        retrieval_metric = retrieval_metrics_by_question.get(question.id, {})

        question_results.append(
            {
                "question_id": question.id,
                "question_text": question.question_text,
                "answer_id": latest_answer.id if latest_answer else None,
                "answer_text": latest_answer.answer_text if latest_answer else None,
                "reviewed": latest_evaluation is not None,
                "overall_score": latest_evaluation.overall_score if latest_evaluation else None,
                "citation_quality_score": latest_evaluation.citation_quality_score if latest_evaluation else None,
                "latency_cost_score": latest_evaluation.latency_cost_score if latest_evaluation else None,
                "evidence_faithfulness_score": latest_evaluation.evidence_faithfulness_score if latest_evaluation else None,
                "answer_relevance_score": latest_evaluation.answer_relevance_score if latest_evaluation else None,
                "retrieval_quality_score": latest_evaluation.retrieval_quality_score if latest_evaluation else None,
                "evaluation_mode": latest_evaluation.evaluation_mode if latest_evaluation else None,
                "judge_model_name": latest_evaluation.judge_model_name if latest_evaluation else None,
                "review_status": latest_evaluation.review_status if latest_evaluation else None,
                "reviewed_by_user_id": latest_evaluation.reviewed_by_user_id if latest_evaluation else None,
                "reviewed_at": latest_evaluation.reviewed_at if latest_evaluation else None,
                "expected_source_match": retrieval_metric.get("expected_source_match"),
                "first_relevant_rank": retrieval_metric.get("first_relevant_rank"),
                "retrieved_chunk_count": retrieval_metric.get("retrieved_chunk_count", 0),
                "precision_at_k": retrieval_metric.get("precision_at_k"),
                "recall_at_k": retrieval_metric.get("recall_at_k"),
                "reciprocal_rank": retrieval_metric.get("reciprocal_rank"),
                "missing_evidence": retrieval_metric.get("missing_evidence", False),
            }
        )

    return {
        "project_id": project.id,
        "run_id": run.id,
        "run_name": run.name,
        "total_questions": len(questions),
        "generated_answers": len(answers),
        "reviewed_answers": len(reviewed_answer_ids),
        "review_completion_percent": percent(len(reviewed_answer_ids), len(answers)),
        "average_overall_score": decimal_average([evaluation.overall_score for evaluation in evaluations]),
        "dimension_averages": dimension_averages,
        "weakest_dimension": weakest_dimension,
        "retrieval_metrics": retrieval_metrics,
        "question_results": question_results,
    }


def build_project_summary(db: Session, project: Project) -> dict[str, object]:
    runs = list(
        db.scalars(
            select(EvaluationRun)
            .where(EvaluationRun.project_id == project.id)
            .order_by(EvaluationRun.created_at.desc(), EvaluationRun.id.desc())
        ).all()
    )

    run_summaries = []
    all_overall_scores: list[Decimal] = []
    for run in runs:
        summary = build_run_summary(db, project, run)
        if summary["average_overall_score"] is not None:
            all_overall_scores.append(summary["average_overall_score"])
        run_summaries.append(
            {
                "run_id": run.id,
                "run_name": run.name,
                "generated_answers": summary["generated_answers"],
                "reviewed_answers": summary["reviewed_answers"],
                "average_overall_score": summary["average_overall_score"],
            }
        )

    scored_runs = [run_summary for run_summary in run_summaries if run_summary["average_overall_score"] is not None]
    best_run = max(scored_runs, key=lambda item: item["average_overall_score"]) if scored_runs else None
    weakest_run = min(scored_runs, key=lambda item: item["average_overall_score"]) if scored_runs else None

    return {
        "project_id": project.id,
        "project_name": project.name,
        "total_runs": len(runs),
        "average_overall_score": decimal_average(all_overall_scores),
        "best_run": best_run,
        "weakest_run": weakest_run,
        "runs": run_summaries,
    }


def score_delta(left: Decimal | None, right: Decimal | None) -> Decimal | None:
    if left is None or right is None:
        return None
    return (left - right).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def decimal_or_zero(value: Decimal | None) -> Decimal:
    return value if value is not None else Decimal("0.00")


def clamp_decimal(value: Decimal, lower: Decimal, upper: Decimal) -> Decimal:
    return max(lower, min(upper, value))


def experiment_quality_gate(
    generated_answers: int,
    reviewed_answers: int,
    average_score: Decimal | None,
    ready_for_release: bool,
    high_error_count: int,
    critical_error_count: int,
) -> str:
    if generated_answers == 0:
        return "no_outputs"
    if critical_error_count > 0:
        return "blocked_critical_errors"
    if high_error_count > 0:
        return "needs_error_review"
    if reviewed_answers < generated_answers:
        return "needs_review"
    if ready_for_release and average_score is not None and average_score >= Decimal("4.00"):
        return "release_candidate"
    return "scored"


def calculate_leaderboard_score(
    average_score: Decimal | None,
    review_completion_percent: Decimal,
    retrieval_hit_rate: Decimal | None,
    judge_within_one_agreement_percent: Decimal,
    judge_paired_answer_count: int,
    error_count: int,
    high_error_count: int,
    critical_error_count: int,
) -> Decimal:
    score_component = decimal_or_zero(average_score) / Decimal("5.00") * Decimal("50.00")
    review_component = review_completion_percent / Decimal("100.00") * Decimal("15.00")
    retrieval_component = decimal_or_zero(retrieval_hit_rate) * Decimal("15.00")
    calibration_component = (
        judge_within_one_agreement_percent / Decimal("100.00") * Decimal("10.00")
        if judge_paired_answer_count > 0
        else Decimal("0.00")
    )
    error_penalty = min(
        Decimal("20.00"),
        (Decimal(error_count) * Decimal("3.00"))
        + (Decimal(high_error_count) * Decimal("2.00"))
        + (Decimal(critical_error_count) * Decimal("5.00")),
    )
    score = score_component + review_component + retrieval_component + calibration_component - error_penalty
    return clamp_decimal(score, Decimal("0.00"), Decimal("100.00")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def build_experiment_leaderboard(db: Session, project: Project) -> dict[str, object]:
    runs = list(
        db.scalars(
            select(EvaluationRun)
            .where(EvaluationRun.project_id == project.id)
            .order_by(EvaluationRun.created_at.desc(), EvaluationRun.id.desc())
        ).all()
    )
    rows = []
    for run in runs:
        summary = build_run_summary(db, project, run)
        review_dashboard = build_run_review_dashboard(db, project, run)
        calibration = build_judge_calibration(db, project, run)
        taxonomy = build_error_taxonomy(db, project, run)
        severity_counts = {item["key"]: item["count"] for item in taxonomy["severity_counts"]}
        high_error_count = int(severity_counts.get("high", 0))
        critical_error_count = int(severity_counts.get("critical", 0))
        average_score = review_dashboard["approved_average_overall_score"] or summary["average_overall_score"]
        leaderboard_score = calculate_leaderboard_score(
            average_score=average_score,
            review_completion_percent=summary["review_completion_percent"],
            retrieval_hit_rate=summary["retrieval_metrics"]["hit_rate"],
            judge_within_one_agreement_percent=calibration["overall_within_one_agreement_percent"],
            judge_paired_answer_count=calibration["paired_answer_count"],
            error_count=taxonomy["total_errors"],
            high_error_count=high_error_count,
            critical_error_count=critical_error_count,
        )
        rows.append(
            {
                "rank": 0,
                "run_id": run.id,
                "run_name": run.name,
                "status": run.status,
                "system_version": run.system_version,
                "retrieval_mode": run.retrieval_mode,
                "generator_model_name": run.generator_model_name,
                "embedding_model_name": run.embedding_model_name,
                "judge_model_name": run.judge_model_name,
                "generated_answers": summary["generated_answers"],
                "reviewed_answers": summary["reviewed_answers"],
                "review_completion_percent": summary["review_completion_percent"],
                "average_overall_score": summary["average_overall_score"],
                "approved_average_overall_score": review_dashboard["approved_average_overall_score"],
                "retrieval_hit_rate": summary["retrieval_metrics"]["hit_rate"],
                "retrieval_mrr": summary["retrieval_metrics"]["mean_reciprocal_rank"],
                "judge_exact_agreement_percent": calibration["overall_exact_agreement_percent"],
                "judge_within_one_agreement_percent": calibration["overall_within_one_agreement_percent"],
                "judge_paired_answer_count": calibration["paired_answer_count"],
                "error_count": taxonomy["total_errors"],
                "high_error_count": high_error_count,
                "critical_error_count": critical_error_count,
                "leaderboard_score": leaderboard_score,
                "quality_gate": experiment_quality_gate(
                    generated_answers=summary["generated_answers"],
                    reviewed_answers=summary["reviewed_answers"],
                    average_score=average_score,
                    ready_for_release=review_dashboard["ready_for_release"],
                    high_error_count=high_error_count,
                    critical_error_count=critical_error_count,
                ),
            }
        )

    ranked_rows = sorted(
        rows,
        key=lambda row: (
            row["leaderboard_score"],
            row["approved_average_overall_score"] or row["average_overall_score"] or Decimal("0.00"),
            row["retrieval_hit_rate"] or Decimal("0.00"),
            -row["error_count"],
            row["run_id"],
        ),
        reverse=True,
    )
    for index, row in enumerate(ranked_rows, start=1):
        row["rank"] = index

    return {
        "project_id": project.id,
        "project_name": project.name,
        "total_runs": len(ranked_rows),
        "best_run_id": ranked_rows[0]["run_id"] if ranked_rows else None,
        "runs": ranked_rows,
    }


def readiness_gate(
    key: str,
    label: str,
    passed: bool,
    observed_value: str | None,
    threshold: str | None,
    pass_message: str,
    fail_message: str,
    required: bool = True,
    warning: bool = False,
) -> dict[str, object]:
    if passed:
        status_value = "pass"
        message = pass_message
    elif warning:
        status_value = "warning"
        message = fail_message
    else:
        status_value = "fail"
        message = fail_message
    return {
        "key": key,
        "label": label,
        "status": status_value,
        "required": required,
        "observed_value": observed_value,
        "threshold": threshold,
        "message": message,
    }


def build_production_readiness(db: Session, project: Project, run: EvaluationRun) -> dict[str, object]:
    summary = build_run_summary(db, project, run)
    review_dashboard = build_run_review_dashboard(db, project, run)
    calibration = build_judge_calibration(db, project, run)
    taxonomy = build_error_taxonomy(db, project, run)
    severity_counts = {item["key"]: item["count"] for item in taxonomy["severity_counts"]}
    high_error_count = int(severity_counts.get("high", 0))
    critical_error_count = int(severity_counts.get("critical", 0))
    approved_average = review_dashboard["approved_average_overall_score"]
    score_for_gate = approved_average or summary["average_overall_score"]
    retrieval_metrics = summary["retrieval_metrics"]
    hit_rate = retrieval_metrics["hit_rate"]
    missing_evidence_count = int(retrieval_metrics["missing_evidence_count"])
    questions_with_expected_source = int(retrieval_metrics["questions_with_expected_source"])
    judge_pairs = int(calibration["paired_answer_count"])
    judge_agreement = calibration["overall_within_one_agreement_percent"]

    gates = [
        readiness_gate(
            key="run_completed",
            label="Run completed",
            passed=run.status == "completed",
            observed_value=run.status,
            threshold="completed",
            pass_message="Run finished successfully.",
            fail_message="Run must complete before production release.",
        ),
        readiness_gate(
            key="answer_coverage",
            label="Answer coverage",
            passed=summary["total_questions"] > 0 and summary["generated_answers"] >= summary["total_questions"],
            observed_value=f"{summary['generated_answers']}/{summary['total_questions']}",
            threshold="all questions answered",
            pass_message="Every test question has a generated answer.",
            fail_message="Generate answers for every test question in scope.",
        ),
        readiness_gate(
            key="human_review_complete",
            label="Human review complete",
            passed=bool(review_dashboard["ready_for_release"]),
            observed_value=f"{review_dashboard['approved_count']}/{review_dashboard['total_answers']} approved",
            threshold="all answers approved",
            pass_message="All generated answers are approved.",
            fail_message="Every generated answer needs an approved evaluation.",
        ),
        readiness_gate(
            key="minimum_score",
            label="Minimum approved score",
            passed=score_for_gate is not None and score_for_gate >= MIN_PRODUCTION_SCORE,
            observed_value=str(score_for_gate) if score_for_gate is not None else None,
            threshold=f">= {MIN_PRODUCTION_SCORE}",
            pass_message="Approved CLEAR-RAG score meets the production threshold.",
            fail_message="Approved CLEAR-RAG score is below the production threshold.",
        ),
        readiness_gate(
            key="retrieval_hit_rate",
            label="Retrieval hit rate",
            passed=hit_rate is not None and hit_rate >= MIN_RETRIEVAL_HIT_RATE,
            observed_value=str(hit_rate) if hit_rate is not None else None,
            threshold=f">= {MIN_RETRIEVAL_HIT_RATE}",
            pass_message="Retriever is finding expected evidence often enough.",
            fail_message=(
                "Add expected sources to questions before enforcing retrieval hit rate."
                if questions_with_expected_source == 0
                else "Retrieval hit rate is below the production threshold."
            ),
            required=questions_with_expected_source > 0,
            warning=questions_with_expected_source == 0,
        ),
        readiness_gate(
            key="missing_evidence",
            label="No missing evidence",
            passed=missing_evidence_count == 0,
            observed_value=str(missing_evidence_count),
            threshold="0",
            pass_message="No expected-source questions are missing evidence.",
            fail_message="Some expected-source questions did not retrieve matching evidence.",
        ),
        readiness_gate(
            key="judge_calibration",
            label="Judge calibration",
            passed=judge_pairs > 0 and judge_agreement >= MIN_JUDGE_WITHIN_ONE_AGREEMENT,
            observed_value=f"{judge_agreement}% across {judge_pairs} pairs",
            threshold=f">= {MIN_JUDGE_WITHIN_ONE_AGREEMENT}% within one point and at least 1 pair",
            pass_message="Automated judge aligns with human scoring.",
            fail_message="Add human calibration scores or improve judge agreement before release.",
        ),
        readiness_gate(
            key="blocking_errors",
            label="No high or critical errors",
            passed=high_error_count == 0 and critical_error_count == 0,
            observed_value=f"{high_error_count} high, {critical_error_count} critical",
            threshold="0 high, 0 critical",
            pass_message="No blocking error-taxonomy findings remain.",
            fail_message="Resolve high and critical error taxonomy findings.",
        ),
    ]
    passed_count = sum(1 for gate in gates if gate["status"] == "pass")
    warning_count = sum(1 for gate in gates if gate["status"] == "warning")
    blocking_failure_count = sum(1 for gate in gates if gate["required"] and gate["status"] == "fail")
    return {
        "project_id": project.id,
        "run_id": run.id,
        "run_name": run.name,
        "ready_for_production": blocking_failure_count == 0,
        "passed_count": passed_count,
        "warning_count": warning_count,
        "blocking_failure_count": blocking_failure_count,
        "gates": gates,
    }


def format_report_value(value: object) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, bool):
        return "yes" if value else "no"
    return str(value)


def report_bullet(label: str, value: object) -> str:
    return f"- {label}: {format_report_value(value)}"


def build_run_report(
    db: Session,
    project: Project,
    run: EvaluationRun,
    payload: ReportBuilderRequest,
) -> dict[str, object]:
    summary = build_run_summary(db, project, run)
    review_dashboard = build_run_review_dashboard(db, project, run)
    readiness = build_production_readiness(db, project, run)
    calibration = build_judge_calibration(db, project, run)
    taxonomy = build_error_taxonomy(db, project, run)
    selected_sections = list(dict.fromkeys(payload.sections))
    title = payload.title or f"{project.name} - {run.name} Evaluation Report"
    generated_at = datetime.now(timezone.utc)

    section_builders = {
        "overview": lambda: "\n".join(
            [
                report_bullet("Project", project.name),
                report_bullet("Run", run.name),
                report_bullet("Audience", payload.audience),
                report_bullet("Run status", run.status),
                report_bullet("System version", run.system_version),
                report_bullet("Retrieval mode", run.retrieval_mode),
                report_bullet("Generator model", run.generator_model_name),
                report_bullet("Judge model", run.judge_model_name),
            ]
        ),
        "readiness": lambda: "\n".join(
            [
                report_bullet("Ready for production", readiness["ready_for_production"]),
                report_bullet("Passed gates", readiness["passed_count"]),
                report_bullet("Warnings", readiness["warning_count"]),
                report_bullet("Blocking failures", readiness["blocking_failure_count"]),
                "",
                *[
                    f"- {gate['label']}: {gate['status']} ({gate['message']})"
                    for gate in readiness["gates"]
                ],
            ]
        ),
        "scores": lambda: "\n".join(
            [
                report_bullet("Generated answers", summary["generated_answers"]),
                report_bullet("Reviewed answers", summary["reviewed_answers"]),
                report_bullet("Review completion", f"{summary['review_completion_percent']}%"),
                report_bullet("Average overall score", summary["average_overall_score"]),
                report_bullet("Approved average score", review_dashboard["approved_average_overall_score"]),
                report_bullet("Weakest dimension", summary["weakest_dimension"]),
                "",
                *[
                    report_bullet(DIMENSION_LABELS[field], summary["dimension_averages"][field])
                    for field in SCORE_FIELDS
                ],
            ]
        ),
        "retrieval": lambda: "\n".join(
            [
                report_bullet("Hit rate", summary["retrieval_metrics"]["hit_rate"]),
                report_bullet("Precision@3", summary["retrieval_metrics"]["precision_at_k"]),
                report_bullet("Recall@3", summary["retrieval_metrics"]["recall_at_k"]),
                report_bullet("Mean reciprocal rank", summary["retrieval_metrics"]["mean_reciprocal_rank"]),
                report_bullet("Chunk coverage", summary["retrieval_metrics"]["chunk_coverage"]),
                report_bullet("Missing evidence count", summary["retrieval_metrics"]["missing_evidence_count"]),
            ]
        ),
        "calibration": lambda: "\n".join(
            [
                report_bullet("Paired answers", calibration["paired_answer_count"]),
                report_bullet("Exact agreement", f"{calibration['overall_exact_agreement_percent']}%"),
                report_bullet("Within-one agreement", f"{calibration['overall_within_one_agreement_percent']}%"),
                report_bullet("Average overall delta", calibration["average_overall_delta"]),
            ]
        ),
        "errors": lambda: "\n".join(
            [
                report_bullet("Total error tags", taxonomy["total_errors"]),
                report_bullet("Affected answers", taxonomy["affected_answers"]),
                "",
                *[
                    f"- {item['label']}: {item['count']} ({item['percent']}%)"
                    for item in taxonomy["category_counts"]
                    if item["count"] > 0
                ],
            ]
        ).strip(),
        "questions": lambda: "\n".join(
            [
                f"- Q{result['question_id']}: {result['question_text']} | score {format_report_value(result['overall_score'])} | retrieval {format_report_value(result['expected_source_match'])} | answer {format_report_value(result['answer_text'])}"
                for result in summary["question_results"]
            ]
        ),
    }
    section_titles = {
        "overview": "Overview",
        "readiness": "Production Readiness",
        "scores": "CLEAR-RAG Scores",
        "retrieval": "Retrieval Evaluation",
        "calibration": "Judge Calibration",
        "errors": "Error Taxonomy",
        "questions": "Question Results",
    }
    sections = [
        {
            "key": section_key,
            "title": section_titles[section_key],
            "content": section_builders[section_key](),
        }
        for section_key in selected_sections
    ]
    markdown_parts = [
        f"# {title}",
        "",
        f"Generated at: {generated_at.isoformat()}",
        f"Audience: {payload.audience}",
        "",
    ]
    for section in sections:
        markdown_parts.extend([f"## {section['title']}", "", section["content"], ""])

    return {
        "project_id": project.id,
        "run_id": run.id,
        "title": title,
        "audience": payload.audience,
        "generated_at": generated_at,
        "sections": sections,
        "markdown": "\n".join(markdown_parts).strip() + "\n",
    }


def better_run_id(run_summaries: list[dict[str, object]], score_key: str = "average_overall_score") -> int | None:
    scored = [summary for summary in run_summaries if summary[score_key] is not None]
    if not scored:
        return None
    best = max(scored, key=lambda item: item[score_key])
    return int(best["run_id"])


def build_run_comparison(db: Session, project: Project, runs: list[EvaluationRun]) -> dict[str, object]:
    summaries = [build_run_summary(db, project, run) for run in runs]
    summary_by_run_id = {summary["run_id"]: summary for summary in summaries}

    run_results = []
    for run in runs:
        summary = summary_by_run_id[run.id]
        run_results.append(
            {
                "run_id": run.id,
                "run_name": run.name,
                "system_version": run.system_version,
                "retrieval_mode": run.retrieval_mode,
                "generator_model_name": run.generator_model_name,
                "embedding_model_name": run.embedding_model_name,
                "judge_model_name": run.judge_model_name,
                "generated_answers": summary["generated_answers"],
                "reviewed_answers": summary["reviewed_answers"],
                "average_overall_score": summary["average_overall_score"],
                "dimension_averages": summary["dimension_averages"],
                "weakest_dimension": summary["weakest_dimension"],
            }
        )

    baseline_summary = summaries[0]
    metric_deltas = {}
    for summary in summaries[1:]:
        metric_deltas[str(summary["run_id"])] = {
            "overall_score_delta": score_delta(summary["average_overall_score"], baseline_summary["average_overall_score"]),
            "citation_quality_delta": score_delta(
                summary["dimension_averages"]["citation_quality_score"],
                baseline_summary["dimension_averages"]["citation_quality_score"],
            ),
            "latency_cost_delta": score_delta(
                summary["dimension_averages"]["latency_cost_score"],
                baseline_summary["dimension_averages"]["latency_cost_score"],
            ),
            "evidence_faithfulness_delta": score_delta(
                summary["dimension_averages"]["evidence_faithfulness_score"],
                baseline_summary["dimension_averages"]["evidence_faithfulness_score"],
            ),
            "answer_relevance_delta": score_delta(
                summary["dimension_averages"]["answer_relevance_score"],
                baseline_summary["dimension_averages"]["answer_relevance_score"],
            ),
            "retrieval_quality_delta": score_delta(
                summary["dimension_averages"]["retrieval_quality_score"],
                baseline_summary["dimension_averages"]["retrieval_quality_score"],
            ),
        }

    question_map: dict[int, dict[str, object]] = {}
    for summary in summaries:
        for result in summary["question_results"]:
            question_entry = question_map.setdefault(
                result["question_id"],
                {
                    "question_id": result["question_id"],
                    "question_text": result["question_text"],
                    "run_results": [],
                },
            )
            question_entry["run_results"].append(
                {
                    "run_id": summary["run_id"],
                    "answer_id": result["answer_id"],
                    "answer_text": result["answer_text"],
                    "overall_score": result["overall_score"],
                    "reviewed": result["reviewed"],
                    "evaluation_mode": result["evaluation_mode"],
                    "judge_model_name": result["judge_model_name"],
                }
            )

    question_results = []
    for item in question_map.values():
        item["best_run_id"] = better_run_id(item["run_results"], score_key="overall_score")
        question_results.append(item)

    return {
        "project_id": project.id,
        "baseline_run_id": runs[0].id,
        "compared_run_ids": [run.id for run in runs],
        "runs": run_results,
        "metric_deltas": metric_deltas,
        "question_results": sorted(question_results, key=lambda item: item["question_id"]),
    }


def build_run_review_dashboard(db: Session, project: Project, run: EvaluationRun) -> dict[str, object]:
    questions = {
        question.id: question
        for question in db.scalars(select(TestQuestion).where(TestQuestion.project_id == project.id)).all()
    }
    answers = list(
        db.scalars(
            select(GeneratedAnswer)
            .where(GeneratedAnswer.evaluation_run_id == run.id)
            .order_by(GeneratedAnswer.created_at.asc(), GeneratedAnswer.id.asc())
        ).all()
    )
    evaluations_by_answer: dict[int, list[EvaluationRecord]] = {}
    for evaluation in db.scalars(
        select(EvaluationRecord)
        .where(EvaluationRecord.evaluation_run_id == run.id)
        .order_by(EvaluationRecord.created_at.asc(), EvaluationRecord.id.asc())
    ).all():
        evaluations_by_answer.setdefault(evaluation.generated_answer_id, []).append(evaluation)

    chunks_by_question: dict[int, list[RetrievedChunk]] = {}
    for chunk in db.scalars(
        select(RetrievedChunk)
        .where(RetrievedChunk.evaluation_run_id == run.id)
        .order_by(RetrievedChunk.test_question_id.asc(), RetrievedChunk.rank.asc(), RetrievedChunk.id.asc())
    ).all():
        chunks_by_question.setdefault(chunk.test_question_id, []).append(chunk)

    items = []
    approved_scores: list[Decimal] = []
    status_counts = {"pending_review": 0, "approved": 0, "needs_revision": 0}
    for answer in answers:
        question = questions.get(answer.test_question_id)
        if question is None:
            continue
        latest_evaluation = latest_by_id(evaluations_by_answer.get(answer.id, []))
        review_status = latest_evaluation.review_status if latest_evaluation else "pending_review"
        status_counts[review_status] += 1
        if latest_evaluation and latest_evaluation.review_status == "approved":
            approved_scores.append(latest_evaluation.overall_score)

        items.append(
            {
                "question_id": question.id,
                "question_text": question.question_text,
                "question_type": question.question_type,
                "expected_source": question.expected_source,
                "answer_id": answer.id,
                "answer_text": answer.answer_text,
                "model_name": answer.model_name,
                "evaluation_id": latest_evaluation.id if latest_evaluation else None,
                "evaluation_mode": latest_evaluation.evaluation_mode if latest_evaluation else None,
                "review_status": review_status,
                "overall_score": latest_evaluation.overall_score if latest_evaluation else None,
                "citation_quality_score": latest_evaluation.citation_quality_score if latest_evaluation else None,
                "latency_cost_score": latest_evaluation.latency_cost_score if latest_evaluation else None,
                "evidence_faithfulness_score": latest_evaluation.evidence_faithfulness_score if latest_evaluation else None,
                "answer_relevance_score": latest_evaluation.answer_relevance_score if latest_evaluation else None,
                "retrieval_quality_score": latest_evaluation.retrieval_quality_score if latest_evaluation else None,
                "judge_model_name": latest_evaluation.judge_model_name if latest_evaluation else None,
                "judge_reasoning": latest_evaluation.judge_reasoning if latest_evaluation else None,
                "reviewer_notes": latest_evaluation.reviewer_notes if latest_evaluation else None,
                "suggested_improvement": latest_evaluation.suggested_improvement if latest_evaluation else None,
                "review_notes": latest_evaluation.review_notes if latest_evaluation else None,
                "score_change_reason": latest_evaluation.score_change_reason if latest_evaluation else None,
                "reviewed_by_user_id": latest_evaluation.reviewed_by_user_id if latest_evaluation else None,
                "reviewed_at": latest_evaluation.reviewed_at if latest_evaluation else None,
                "retrieved_chunks": [
                    {
                        "id": chunk.id,
                        "rank": chunk.rank,
                        "source_document_id": chunk.source_document_id,
                        "section_reference": chunk.section_reference,
                        "relevance_label": chunk.relevance_label,
                        "chunk_text": chunk.chunk_text,
                    }
                    for chunk in chunks_by_question.get(question.id, [])
                ],
            }
        )

    total_answers = len(items)
    approved_count = status_counts["approved"]
    return {
        "project_id": project.id,
        "run_id": run.id,
        "run_name": run.name,
        "total_answers": total_answers,
        "pending_review_count": status_counts["pending_review"],
        "approved_count": approved_count,
        "needs_revision_count": status_counts["needs_revision"],
        "review_completion_percent": percent(approved_count, total_answers),
        "ready_for_release": total_answers > 0 and approved_count == total_answers,
        "approved_average_overall_score": decimal_average(approved_scores),
        "items": items,
    }


def bias_direction_for_delta(average_delta: Decimal | None) -> str:
    if average_delta is None or average_delta == Decimal("0.00"):
        return "aligned"
    if average_delta > Decimal("0.00"):
        return "automated_under_scores"
    return "automated_over_scores"


def latest_human_calibration_record(records: list[EvaluationRecord]) -> EvaluationRecord | None:
    human_records = [record for record in records if record.evaluation_mode == "human"]
    approved_records = [record for record in human_records if record.review_status == "approved"]
    return latest_by_id(approved_records or human_records)


def build_judge_calibration(db: Session, project: Project, run: EvaluationRun) -> dict[str, object]:
    questions = {
        question.id: question
        for question in db.scalars(select(TestQuestion).where(TestQuestion.project_id == project.id)).all()
    }
    answers = list(
        db.scalars(
            select(GeneratedAnswer)
            .where(GeneratedAnswer.evaluation_run_id == run.id)
            .order_by(GeneratedAnswer.created_at.asc(), GeneratedAnswer.id.asc())
        ).all()
    )
    evaluations_by_answer: dict[int, list[EvaluationRecord]] = {}
    for evaluation in db.scalars(
        select(EvaluationRecord)
        .where(EvaluationRecord.evaluation_run_id == run.id)
        .order_by(EvaluationRecord.created_at.asc(), EvaluationRecord.id.asc())
    ).all():
        evaluations_by_answer.setdefault(evaluation.generated_answer_id, []).append(evaluation)

    answer_comparisons = []
    overall_deltas: list[Decimal] = []
    exact_match_count = 0
    within_one_match_count = 0
    total_score_pairs = 0
    dimension_deltas: dict[str, list[Decimal]] = {field: [] for field in SCORE_FIELDS}
    dimension_exact_counts: dict[str, int] = {field: 0 for field in SCORE_FIELDS}
    dimension_within_one_counts: dict[str, int] = {field: 0 for field in SCORE_FIELDS}
    dimension_automated_higher_counts: dict[str, int] = {field: 0 for field in SCORE_FIELDS}
    dimension_human_higher_counts: dict[str, int] = {field: 0 for field in SCORE_FIELDS}
    dimension_equal_counts: dict[str, int] = {field: 0 for field in SCORE_FIELDS}
    automated_answer_ids: set[int] = set()
    human_answer_ids: set[int] = set()

    for answer in answers:
        records = evaluations_by_answer.get(answer.id, [])
        automated_evaluation = latest_by_id([record for record in records if record.evaluation_mode == "automated"])
        human_evaluation = latest_human_calibration_record(records)
        if automated_evaluation is not None:
            automated_answer_ids.add(answer.id)
        if human_evaluation is not None:
            human_answer_ids.add(answer.id)
        if automated_evaluation is None or human_evaluation is None:
            continue

        question = questions.get(answer.test_question_id)
        if question is None:
            continue

        per_answer_deltas = {}
        exact_matches = {}
        within_one_matches = {}
        for field in SCORE_FIELDS:
            automated_score = Decimal(getattr(automated_evaluation, field))
            human_score = Decimal(getattr(human_evaluation, field))
            delta = (human_score - automated_score).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            exact_match = delta == Decimal("0.00")
            within_one_match = abs(delta) <= Decimal("1.00")

            per_answer_deltas[field] = delta
            exact_matches[field] = exact_match
            within_one_matches[field] = within_one_match
            dimension_deltas[field].append(delta)
            total_score_pairs += 1
            if exact_match:
                exact_match_count += 1
                dimension_exact_counts[field] += 1
                dimension_equal_counts[field] += 1
            elif delta > Decimal("0.00"):
                dimension_human_higher_counts[field] += 1
            else:
                dimension_automated_higher_counts[field] += 1
            if within_one_match:
                within_one_match_count += 1
                dimension_within_one_counts[field] += 1

        overall_delta = (human_evaluation.overall_score - automated_evaluation.overall_score).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )
        overall_deltas.append(overall_delta)
        answer_comparisons.append(
            {
                "question_id": question.id,
                "question_text": question.question_text,
                "answer_id": answer.id,
                "automated_evaluation_id": automated_evaluation.id,
                "human_evaluation_id": human_evaluation.id,
                "automated_overall_score": automated_evaluation.overall_score,
                "human_overall_score": human_evaluation.overall_score,
                "overall_delta": overall_delta,
                "dimension_deltas": per_answer_deltas,
                "exact_matches": exact_matches,
                "within_one_matches": within_one_matches,
            }
        )

    dimension_calibration = []
    for field in SCORE_FIELDS:
        score_pair_count = len(dimension_deltas[field])
        average_delta = decimal_average(dimension_deltas[field])
        dimension_calibration.append(
            {
                "field": field,
                "label": DIMENSION_LABELS[field],
                "paired_score_count": score_pair_count,
                "average_delta": average_delta,
                "exact_agreement_percent": percent(dimension_exact_counts[field], score_pair_count),
                "within_one_agreement_percent": percent(dimension_within_one_counts[field], score_pair_count),
                "automated_higher_count": dimension_automated_higher_counts[field],
                "human_higher_count": dimension_human_higher_counts[field],
                "equal_count": dimension_equal_counts[field],
                "bias_direction": bias_direction_for_delta(average_delta),
            }
        )

    return {
        "project_id": project.id,
        "run_id": run.id,
        "run_name": run.name,
        "paired_answer_count": len(answer_comparisons),
        "automated_only_count": len(automated_answer_ids - human_answer_ids),
        "human_only_count": len(human_answer_ids - automated_answer_ids),
        "overall_exact_agreement_percent": percent(exact_match_count, total_score_pairs),
        "overall_within_one_agreement_percent": percent(within_one_match_count, total_score_pairs),
        "average_overall_delta": decimal_average(overall_deltas),
        "dimension_calibration": dimension_calibration,
        "answer_comparisons": sorted(answer_comparisons, key=lambda item: item["question_id"]),
    }


def build_count_buckets(counts: dict[str, int], labels: dict[str, str], total: int) -> list[dict[str, object]]:
    return [
        {
            "key": key,
            "label": labels[key],
            "count": count,
            "percent": percent(count, total),
        }
        for key, count in counts.items()
    ]


def build_error_taxonomy(db: Session, project: Project, run: EvaluationRun) -> dict[str, object]:
    questions = {
        question.id: question
        for question in db.scalars(select(TestQuestion).where(TestQuestion.project_id == project.id)).all()
    }
    answers = {
        answer.id: answer
        for answer in db.scalars(
            select(GeneratedAnswer)
            .where(GeneratedAnswer.evaluation_run_id == run.id)
            .order_by(GeneratedAnswer.created_at.asc(), GeneratedAnswer.id.asc())
        ).all()
    }
    annotations = list(
        db.scalars(
            select(ErrorAnnotation)
            .where(ErrorAnnotation.evaluation_run_id == run.id)
            .order_by(ErrorAnnotation.created_at.desc(), ErrorAnnotation.id.desc())
        ).all()
    )
    category_counts = {key: 0 for key in ERROR_CATEGORY_LABELS}
    severity_counts = {key: 0 for key in ERROR_SEVERITY_LABELS}
    items = []
    affected_answer_ids: set[int] = set()
    for annotation in annotations:
        question = questions.get(annotation.test_question_id)
        answer = answers.get(annotation.generated_answer_id)
        if question is None or answer is None:
            continue
        category_counts[annotation.category] += 1
        severity_counts[annotation.severity] += 1
        affected_answer_ids.add(annotation.generated_answer_id)
        items.append(
            {
                "id": annotation.id,
                "question_id": question.id,
                "question_text": question.question_text,
                "answer_id": answer.id,
                "answer_text": answer.answer_text,
                "evaluation_record_id": annotation.evaluation_record_id,
                "category": annotation.category,
                "category_label": ERROR_CATEGORY_LABELS[annotation.category],
                "severity": annotation.severity,
                "source": annotation.source,
                "notes": annotation.notes,
                "evidence_reference": annotation.evidence_reference,
                "created_by_user_id": annotation.created_by_user_id,
                "created_at": annotation.created_at,
            }
        )

    total_errors = len(items)
    return {
        "project_id": project.id,
        "run_id": run.id,
        "run_name": run.name,
        "total_errors": total_errors,
        "affected_answers": len(affected_answer_ids),
        "category_counts": build_count_buckets(category_counts, ERROR_CATEGORY_LABELS, total_errors),
        "severity_counts": build_count_buckets(severity_counts, ERROR_SEVERITY_LABELS, total_errors),
        "items": items,
    }


def apply_updates(instance: object, payload: object) -> None:
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(instance, key, value)


def ensure_valid_document_source(document: SourceDocument) -> None:
    if document.source_kind == "uri" and not document.source_uri:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="source_uri is required for URI-based documents",
        )
    if document.source_kind == "file" and not document.storage_path:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="storage_path is required for file-based documents",
        )


def get_upload_root() -> Path:
    settings = get_settings()
    upload_root = Path(settings.upload_dir)
    if upload_root.is_absolute():
        return upload_root
    return BACKEND_ROOT / upload_root


def sanitize_filename(filename: str) -> str:
    path_name = Path(filename).name
    return re.sub(r"[^A-Za-z0-9._-]", "_", path_name).strip("._") or "uploaded-document"


def normalize_question_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().lower()


def validate_question_import_file(file: UploadFile) -> str:
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Uploaded import file must have a filename")
    safe_name = sanitize_filename(file.filename)
    extension = Path(safe_name).suffix.lower()
    if extension not in ALLOWED_QUESTION_IMPORT_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported question import type. Allowed: {', '.join(sorted(ALLOWED_QUESTION_IMPORT_EXTENSIONS))}",
        )
    return safe_name


def parse_question_import_rows(file_name: str, content: bytes) -> list[dict[str, object]]:
    extension = Path(file_name).suffix.lower()
    text = content.decode("utf-8-sig", errors="ignore")
    if extension == ".csv":
        reader = csv.DictReader(io.StringIO(text))
        fieldnames = {field.strip() for field in (reader.fieldnames or []) if field}
        missing_columns = QUESTION_IMPORT_REQUIRED_COLUMNS - fieldnames
        if missing_columns:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Missing required columns: {', '.join(sorted(missing_columns))}",
            )
        return [{"row_number": index, **row} for index, row in enumerate(reader, start=2)]

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid JSON import file") from exc
    rows = parsed.get("questions") if isinstance(parsed, dict) else parsed
    if not isinstance(rows, list):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="JSON import must be an array or an object with a questions array",
        )
    return [
        {"row_number": index, **row}
        for index, row in enumerate(rows, start=1)
        if isinstance(row, dict)
    ]


def validate_question_import_row(row: dict[str, object]) -> tuple[str, str, str | None]:
    question_text = str(row.get("question_text") or "").strip()
    question_type = str(row.get("question_type") or "").strip()
    expected_source = str(row.get("expected_source") or "").strip() or None
    if not question_text:
        raise ValueError("question_text is required")
    if question_type not in QUESTION_TYPES:
        raise ValueError(f"question_type must be one of: {', '.join(sorted(QUESTION_TYPES))}")
    if expected_source and len(expected_source) > 255:
        raise ValueError("expected_source must be 255 characters or fewer")
    return question_text, question_type, expected_source


def validate_upload_file(file: UploadFile) -> str:
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Uploaded file must have a filename")

    safe_name = sanitize_filename(file.filename)
    extension = Path(safe_name).suffix.lower()
    if extension not in ALLOWED_UPLOAD_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported file type. Allowed: {', '.join(sorted(ALLOWED_UPLOAD_EXTENSIONS))}",
        )
    return safe_name


def remove_stored_file(document: SourceDocument) -> None:
    if document.source_kind != "file" or not document.storage_path:
        return

    file_path = get_upload_root() / document.storage_path
    try:
        if file_path.is_file():
            file_path.unlink()
    except OSError:
        pass


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: WritableUser,
) -> Project:
    project = Project(**payload.model_dump(), created_by_user_id=current_user.id)
    db.add(project)
    db.flush()
    create_audit_event(
        db,
        current_user,
        event_type="project_created",
        entity_type="project",
        entity_id=project.id,
        project_id=project.id,
        event_summary=f"Project '{project.name}' was created.",
        metadata={"system_type": project.system_type, "target_users": project.target_users},
    )
    db.commit()
    db.refresh(project)
    return project


@router.get("", response_model=list[ProjectRead])
def list_projects(
    db: Annotated[Session, Depends(get_db)],
    _: AuthenticatedUser,
) -> list[Project]:
    return list(db.scalars(select(Project).order_by(Project.created_at.desc(), Project.id.desc())).all())


@router.get("/{project_id}", response_model=ProjectRead)
def read_project(
    project_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: AuthenticatedUser,
) -> Project:
    return get_project_or_404(db, project_id)


@router.get("/{project_id}/summary", response_model=ProjectSummaryRead)
def read_project_summary(
    project_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: AuthenticatedUser,
) -> dict[str, object]:
    project = get_project_or_404(db, project_id)
    return build_project_summary(db, project)


@router.get("/{project_id}/leaderboard", response_model=ExperimentLeaderboardRead)
def read_experiment_leaderboard(
    project_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: AuthenticatedUser,
) -> dict[str, object]:
    project = get_project_or_404(db, project_id)
    return build_experiment_leaderboard(db, project)


@router.get("/{project_id}/governance-summary", response_model=GovernanceSummaryRead)
def read_governance_summary(
    project_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: AuthenticatedUser,
) -> dict[str, object]:
    project = get_project_or_404(db, project_id)
    return build_governance_summary(db, project)


@router.get("/{project_id}/audit-events", response_model=list[AuditEventRead])
def list_project_audit_events(
    project_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: AuthenticatedUser,
) -> list[AuditEvent]:
    get_project_or_404(db, project_id)
    return list(
        db.scalars(
            select(AuditEvent)
            .where(AuditEvent.project_id == project_id)
            .order_by(AuditEvent.created_at.desc(), AuditEvent.id.desc())
        ).all()
    )


@router.get("/{project_id}/background-jobs", response_model=list[BackgroundJobRead])
def list_project_background_jobs(
    project_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: AuthenticatedUser,
) -> list[BackgroundJob]:
    get_project_or_404(db, project_id)
    return list(
        db.scalars(
            select(BackgroundJob)
            .where(BackgroundJob.project_id == project_id)
            .order_by(BackgroundJob.created_at.desc(), BackgroundJob.id.desc())
        ).all()
    )


@router.get("/{project_id}/background-jobs/{job_id}", response_model=BackgroundJobRead)
def read_background_job(
    project_id: int,
    job_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: AuthenticatedUser,
) -> BackgroundJob:
    get_project_or_404(db, project_id)
    return get_background_job_or_404(db, project_id, job_id)


@router.patch("/{project_id}", response_model=ProjectRead)
def update_project(
    project_id: int,
    payload: ProjectUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: WritableUser,
) -> Project:
    project = get_project_or_404(db, project_id)
    apply_updates(project, payload)
    create_audit_event(
        db,
        current_user,
        event_type="project_updated",
        entity_type="project",
        entity_id=project.id,
        project_id=project.id,
        event_summary=f"Project '{project.name}' settings were updated.",
        metadata=payload.model_dump(exclude_unset=True),
    )
    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: WritableUser,
) -> Response:
    project = get_project_or_404(db, project_id)
    for document in project.source_documents:
        remove_stored_file(document)
    db.delete(project)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{project_id}/documents", response_model=SourceDocumentRead, status_code=status.HTTP_201_CREATED)
def create_document(
    project_id: int,
    payload: SourceDocumentCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: WritableUser,
) -> SourceDocument:
    get_project_or_404(db, project_id)
    document = SourceDocument(**payload.model_dump(), project_id=project_id)
    ensure_valid_document_source(document)
    db.add(document)
    db.flush()
    create_audit_event(
        db,
        current_user,
        event_type="document_registered",
        entity_type="source_document",
        entity_id=document.id,
        project_id=project_id,
        event_summary=f"Source document '{document.title}' was registered by URI.",
        metadata={"document_type": document.document_type, "source_kind": document.source_kind},
    )
    db.commit()
    db.refresh(document)
    return document


@router.post("/{project_id}/documents/upload", response_model=SourceDocumentRead, status_code=status.HTTP_201_CREATED)
def upload_document(
    project_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: WritableUser,
    title: Annotated[str, Form(min_length=1, max_length=255)],
    document_type: Annotated[str, Form(min_length=1, max_length=80)],
    file: Annotated[UploadFile, File()],
    version: Annotated[str | None, Form(max_length=80)] = None,
) -> SourceDocument:
    get_project_or_404(db, project_id)
    safe_original_name = validate_upload_file(file)
    stored_file_name = f"{uuid4().hex}_{safe_original_name}"
    relative_storage_path = Path("documents") / str(project_id) / stored_file_name
    absolute_storage_path = get_upload_root() / relative_storage_path
    absolute_storage_path.parent.mkdir(parents=True, exist_ok=True)

    file_size = 0
    with absolute_storage_path.open("wb") as output:
        while chunk := file.file.read(1024 * 1024):
            file_size += len(chunk)
            output.write(chunk)

    document = SourceDocument(
        project_id=project_id,
        title=title,
        document_type=document_type,
        source_kind="file",
        version=version,
        original_file_name=safe_original_name,
        stored_file_name=stored_file_name,
        content_type=file.content_type,
        file_size_bytes=file_size,
        storage_path=str(relative_storage_path).replace("\\", "/"),
    )
    ensure_valid_document_source(document)
    db.add(document)
    db.flush()
    create_audit_event(
        db,
        current_user,
        event_type="document_uploaded",
        entity_type="source_document",
        entity_id=document.id,
        project_id=project_id,
        event_summary=f"Source document '{document.title}' was uploaded.",
        metadata={
            "document_type": document.document_type,
            "original_file_name": document.original_file_name,
            "file_size_bytes": document.file_size_bytes,
            "content_type": document.content_type,
        },
    )
    db.commit()
    db.refresh(document)
    return document


@router.get("/{project_id}/documents", response_model=list[SourceDocumentRead])
def list_documents(
    project_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: AuthenticatedUser,
) -> list[SourceDocument]:
    get_project_or_404(db, project_id)
    return list(
        db.scalars(
            select(SourceDocument)
            .where(SourceDocument.project_id == project_id)
            .order_by(SourceDocument.created_at.desc(), SourceDocument.id.desc())
        ).all()
    )


@router.get("/{project_id}/documents/{document_id}", response_model=SourceDocumentRead)
def read_document(
    project_id: int,
    document_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: AuthenticatedUser,
) -> SourceDocument:
    get_project_or_404(db, project_id)
    return get_document_or_404(db, project_id, document_id)


@router.patch("/{project_id}/documents/{document_id}", response_model=SourceDocumentRead)
def update_document(
    project_id: int,
    document_id: int,
    payload: SourceDocumentUpdate,
    db: Annotated[Session, Depends(get_db)],
    _: WritableUser,
) -> SourceDocument:
    get_project_or_404(db, project_id)
    document = get_document_or_404(db, project_id, document_id)
    apply_updates(document, payload)
    ensure_valid_document_source(document)
    db.commit()
    db.refresh(document)
    return document


@router.delete("/{project_id}/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    project_id: int,
    document_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: WritableUser,
) -> Response:
    get_project_or_404(db, project_id)
    document = get_document_or_404(db, project_id, document_id)
    remove_stored_file(document)
    db.delete(document)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{project_id}/documents/{document_id}/index", response_model=DocumentIndexRead)
def index_document(
    project_id: int,
    document_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: WritableUser,
) -> dict[str, object]:
    get_project_or_404(db, project_id)
    document = get_document_or_404(db, project_id, document_id)
    try:
        result = index_source_document(db, document, get_settings())
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    return {
        "document_id": result.document_id,
        "chunks_indexed": result.chunks_indexed,
        "embedding_model": result.embedding_model,
        "message": result.message,
    }


@router.get("/{project_id}/documents/{document_id}/chunks", response_model=list[DocumentChunkRead])
def list_document_chunks(
    project_id: int,
    document_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: AuthenticatedUser,
) -> list[DocumentChunk]:
    get_project_or_404(db, project_id)
    get_document_or_404(db, project_id, document_id)
    return list(
        db.scalars(
            select(DocumentChunk)
            .where(DocumentChunk.source_document_id == document_id)
            .order_by(DocumentChunk.chunk_index.asc(), DocumentChunk.id.asc())
        ).all()
    )


@router.post("/{project_id}/questions", response_model=TestQuestionRead, status_code=status.HTTP_201_CREATED)
def create_question(
    project_id: int,
    payload: TestQuestionCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: WritableUser,
) -> TestQuestion:
    get_project_or_404(db, project_id)
    question = TestQuestion(**payload.model_dump(), project_id=project_id, created_by_user_id=current_user.id)
    db.add(question)
    db.flush()
    create_audit_event(
        db,
        current_user,
        event_type="question_created",
        entity_type="test_question",
        entity_id=question.id,
        project_id=project_id,
        question_id=question.id,
        event_summary="A test question was added.",
        metadata={"question_type": question.question_type, "expected_source": question.expected_source},
    )
    db.commit()
    db.refresh(question)
    return question


@router.get("/{project_id}/questions", response_model=list[TestQuestionRead])
def list_questions(
    project_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: AuthenticatedUser,
) -> list[TestQuestion]:
    get_project_or_404(db, project_id)
    return list(
        db.scalars(
            select(TestQuestion)
            .where(TestQuestion.project_id == project_id)
            .order_by(TestQuestion.created_at.desc(), TestQuestion.id.desc())
        ).all()
    )


@router.get("/{project_id}/questions/{question_id}", response_model=TestQuestionRead)
def read_question(
    project_id: int,
    question_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: AuthenticatedUser,
) -> TestQuestion:
    get_project_or_404(db, project_id)
    return get_question_or_404(db, project_id, question_id)


@router.patch("/{project_id}/questions/{question_id}", response_model=TestQuestionRead)
def update_question(
    project_id: int,
    question_id: int,
    payload: TestQuestionUpdate,
    db: Annotated[Session, Depends(get_db)],
    _: WritableUser,
) -> TestQuestion:
    get_project_or_404(db, project_id)
    question = get_question_or_404(db, project_id, question_id)
    apply_updates(question, payload)
    db.commit()
    db.refresh(question)
    return question


@router.delete("/{project_id}/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_question(
    project_id: int,
    question_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: WritableUser,
) -> Response:
    get_project_or_404(db, project_id)
    question = get_question_or_404(db, project_id, question_id)
    db.delete(question)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{project_id}/question-datasets/import",
    response_model=QuestionImportRead,
    status_code=status.HTTP_201_CREATED,
)
def import_question_dataset(
    project_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: WritableUser,
    dataset_name: Annotated[str, Form(min_length=1, max_length=255)],
    file: Annotated[UploadFile, File()],
    dataset_version: Annotated[str | None, Form(max_length=80)] = None,
) -> dict[str, object]:
    get_project_or_404(db, project_id)
    safe_file_name = validate_question_import_file(file)
    rows = parse_question_import_rows(safe_file_name, file.file.read())
    existing_questions = set(
        normalize_question_text(question)
        for question in db.scalars(select(TestQuestion.question_text).where(TestQuestion.project_id == project_id)).all()
    )
    seen_questions: set[str] = set()

    dataset = QuestionDataset(
        project_id=project_id,
        dataset_name=dataset_name,
        dataset_version=dataset_version,
        imported_file_name=safe_file_name,
        question_count=0,
        created_by_user_id=current_user.id,
    )
    db.add(dataset)
    db.flush()

    questions_imported = 0
    duplicate_questions = 0
    errors: list[dict[str, object]] = []
    for row in rows:
        row_number = int(row.get("row_number") or 0)
        try:
            question_text, question_type, expected_source = validate_question_import_row(row)
        except ValueError as exc:
            errors.append({"row_number": row_number, "message": str(exc)})
            continue

        normalized_text = normalize_question_text(question_text)
        if normalized_text in existing_questions or normalized_text in seen_questions:
            duplicate_questions += 1
            continue

        db.add(
            TestQuestion(
                project_id=project_id,
                dataset_id=dataset.id,
                question_text=question_text,
                question_type=question_type,
                expected_source=expected_source,
                created_by_user_id=current_user.id,
            )
        )
        seen_questions.add(normalized_text)
        questions_imported += 1

    dataset.question_count = questions_imported
    db.commit()
    db.refresh(dataset)
    return {
        "dataset": dataset,
        "questions_imported": questions_imported,
        "duplicate_questions": duplicate_questions,
        "invalid_rows": len(errors),
        "errors": errors,
    }


@router.get("/{project_id}/question-datasets", response_model=list[QuestionDatasetRead])
def list_question_datasets(
    project_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: AuthenticatedUser,
) -> list[QuestionDataset]:
    get_project_or_404(db, project_id)
    return list(
        db.scalars(
            select(QuestionDataset)
            .where(QuestionDataset.project_id == project_id)
            .order_by(QuestionDataset.created_at.desc(), QuestionDataset.id.desc())
        ).all()
    )


@router.post("/{project_id}/batch-experiments", response_model=BatchExperimentRead, status_code=status.HTTP_201_CREATED)
def create_batch_experiment(
    project_id: int,
    payload: BatchExperimentCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: WritableUser,
) -> dict[str, object]:
    project = get_project_or_404(db, project_id)
    dataset = get_dataset_or_404(db, project_id, payload.dataset_id)
    if dataset.question_count <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Selected dataset has no imported questions.",
        )
    if db.scalar(select(TestQuestion.id).where(TestQuestion.dataset_id == dataset.id).limit(1)) is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Selected dataset has no test questions.",
        )

    unique_document_ids = list(dict.fromkeys(payload.document_ids))
    documents = get_documents_or_404(db, project_id, unique_document_ids)
    settings = get_settings()
    now = datetime.now(timezone.utc)
    run = EvaluationRun(
        project_id=project_id,
        name=payload.run_name,
        system_version=payload.system_version,
        notes=payload.notes,
        dataset_id=dataset.id,
        batch_document_ids=json.dumps(unique_document_ids),
        auto_evaluate_enabled=payload.auto_evaluate,
        batch_status="running",
        current_step="creating_run",
        completed_steps=json.dumps([]),
        batch_started_at=now,
        created_by_user_id=current_user.id,
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    auto_evaluation = None
    try:
        if payload.index_documents:
            set_batch_step(run, "index_documents", "creating_run")
            db.commit()
            for document in documents:
                index_source_document(db, document, settings)
            db.refresh(run)

        set_batch_step(run, "rag_execution", "index_documents" if payload.index_documents else "creating_run")
        db.commit()
        rag_result = execute_rag_run(
            db,
            run,
            settings,
            retrieval_mode=payload.retrieval_mode,
            dataset_id=dataset.id,
            document_ids=unique_document_ids,
        )
        rag_execution = {
            "run_id": rag_result.run_id,
            "status": rag_result.status,
            "model_name": rag_result.model_name,
            "processed_questions": rag_result.processed_questions,
            "retrieved_chunks_created": rag_result.retrieved_chunks_created,
            "generated_answers_created": rag_result.generated_answers_created,
            "retrieval_mode": rag_result.retrieval_mode,
            "message": rag_result.message,
        }

        if payload.auto_evaluate:
            set_batch_step(run, "automated_evaluation", "rag_execution")
            db.commit()
            auto_evaluation = run_automated_clear_rag_evaluation(db, project_id, run, current_user)
            db.refresh(run)
            completed_step = "automated_evaluation"
        else:
            completed_step = "rag_execution"

        set_batch_step(run, "completed", completed_step)
        run.batch_status = "completed"
        run.failed_step = None
        run.batch_error_message = None
        run.batch_completed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(run)
    except RagExecutionError as exc:
        db.rollback()
        failed_run = db.get(EvaluationRun, run.id)
        if failed_run is not None:
            failed_run.batch_status = "failed"
            failed_run.failed_step = failed_run.current_step
            failed_run.batch_error_message = exc.message
            failed_run.batch_completed_at = datetime.now(timezone.utc)
            db.commit()
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except HTTPException as exc:
        db.rollback()
        failed_run = db.get(EvaluationRun, run.id)
        if failed_run is not None:
            failed_run.batch_status = "failed"
            failed_run.failed_step = failed_run.current_step
            failed_run.batch_error_message = str(exc.detail)
            failed_run.batch_completed_at = datetime.now(timezone.utc)
            db.commit()
        raise
    except Exception as exc:
        db.rollback()
        failed_run = db.get(EvaluationRun, run.id)
        if failed_run is not None:
            failed_run.batch_status = "failed"
            failed_run.status = "failed"
            failed_run.failed_step = failed_run.current_step
            failed_run.batch_error_message = str(exc)
            failed_run.last_error = str(exc)
            failed_run.batch_completed_at = datetime.now(timezone.utc)
            db.commit()
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    return {
        "run": run,
        "rag_execution": rag_execution,
        "auto_evaluation": auto_evaluation,
        "summary": build_run_summary(db, project, run),
        "message": "Batch experiment completed.",
    }


@router.post("/{project_id}/runs", response_model=EvaluationRunRead, status_code=status.HTTP_201_CREATED)
def create_run(
    project_id: int,
    payload: EvaluationRunCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: WritableUser,
) -> EvaluationRun:
    get_project_or_404(db, project_id)
    run = EvaluationRun(**payload.model_dump(), project_id=project_id, created_by_user_id=current_user.id)
    db.add(run)
    db.flush()
    create_audit_event(
        db,
        current_user,
        event_type="run_created",
        entity_type="evaluation_run",
        entity_id=run.id,
        project_id=project_id,
        run_id=run.id,
        event_summary=f"Evaluation run '{run.name}' was created.",
        metadata={"system_version": run.system_version, "status": run.status},
    )
    db.commit()
    db.refresh(run)
    return run


@router.get("/{project_id}/runs", response_model=list[EvaluationRunRead])
def list_runs(
    project_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: AuthenticatedUser,
) -> list[EvaluationRun]:
    get_project_or_404(db, project_id)
    return list(
        db.scalars(
            select(EvaluationRun)
            .where(EvaluationRun.project_id == project_id)
            .order_by(EvaluationRun.created_at.desc(), EvaluationRun.id.desc())
        ).all()
    )


@router.get("/{project_id}/runs/compare", response_model=RunComparisonRead)
def compare_runs(
    project_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: AuthenticatedUser,
    run_ids: Annotated[list[int], Query(min_length=2)],
) -> dict[str, object]:
    project = get_project_or_404(db, project_id)
    unique_run_ids = list(dict.fromkeys(run_ids))
    if len(unique_run_ids) < 2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Select at least two different runs to compare.",
        )
    runs = list(
        db.scalars(
            select(EvaluationRun)
            .where(EvaluationRun.project_id == project_id, EvaluationRun.id.in_(unique_run_ids))
            .order_by(EvaluationRun.created_at.asc(), EvaluationRun.id.asc())
        ).all()
    )
    found_run_ids = {run.id for run in runs}
    missing_run_ids = [run_id for run_id in unique_run_ids if run_id not in found_run_ids]
    if missing_run_ids:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="One or more runs were not found in this project.")

    ordered_runs = sorted(runs, key=lambda run: unique_run_ids.index(run.id))
    return build_run_comparison(db, project, ordered_runs)


@router.get("/{project_id}/runs/{run_id}", response_model=EvaluationRunRead)
def read_run(
    project_id: int,
    run_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: AuthenticatedUser,
) -> EvaluationRun:
    get_project_or_404(db, project_id)
    return get_run_or_404(db, project_id, run_id)


@router.get("/{project_id}/runs/{run_id}/summary", response_model=RunSummaryRead)
def read_run_summary(
    project_id: int,
    run_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: AuthenticatedUser,
) -> dict[str, object]:
    project = get_project_or_404(db, project_id)
    run = get_run_or_404(db, project_id, run_id)
    return build_run_summary(db, project, run)


@router.get("/{project_id}/runs/{run_id}/retrieval-metrics", response_model=RetrievalMetricsRead)
def read_run_retrieval_metrics(
    project_id: int,
    run_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: AuthenticatedUser,
) -> dict[str, object]:
    project = get_project_or_404(db, project_id)
    run = get_run_or_404(db, project_id, run_id)
    summary = build_run_summary(db, project, run)
    return summary["retrieval_metrics"]


@router.get("/{project_id}/runs/{run_id}/review-dashboard", response_model=RunReviewDashboardRead)
def read_run_review_dashboard(
    project_id: int,
    run_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: AuthenticatedUser,
) -> dict[str, object]:
    project = get_project_or_404(db, project_id)
    run = get_run_or_404(db, project_id, run_id)
    return build_run_review_dashboard(db, project, run)


@router.get("/{project_id}/runs/{run_id}/judge-calibration", response_model=JudgeCalibrationRead)
def read_run_judge_calibration(
    project_id: int,
    run_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: AuthenticatedUser,
) -> dict[str, object]:
    project = get_project_or_404(db, project_id)
    run = get_run_or_404(db, project_id, run_id)
    return build_judge_calibration(db, project, run)


@router.get("/{project_id}/runs/{run_id}/error-taxonomy", response_model=ErrorTaxonomyRead)
def read_run_error_taxonomy(
    project_id: int,
    run_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: AuthenticatedUser,
) -> dict[str, object]:
    project = get_project_or_404(db, project_id)
    run = get_run_or_404(db, project_id, run_id)
    return build_error_taxonomy(db, project, run)


@router.get("/{project_id}/runs/{run_id}/production-readiness", response_model=ProductionReadinessRead)
def read_run_production_readiness(
    project_id: int,
    run_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: AuthenticatedUser,
) -> dict[str, object]:
    project = get_project_or_404(db, project_id)
    run = get_run_or_404(db, project_id, run_id)
    return build_production_readiness(db, project, run)


@router.post("/{project_id}/runs/{run_id}/report", response_model=ReportBuilderRead)
def build_report(
    project_id: int,
    run_id: int,
    payload: ReportBuilderRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: AuthenticatedUser,
) -> dict[str, object]:
    project = get_project_or_404(db, project_id)
    run = get_run_or_404(db, project_id, run_id)
    report = build_run_report(db, project, run, payload)
    create_audit_event(
        db,
        current_user,
        event_type="report_built",
        entity_type="report",
        entity_id=run.id,
        project_id=project_id,
        run_id=run_id,
        event_summary=f"Report '{report['title']}' was generated for run '{run.name}'.",
        metadata={"audience": payload.audience, "sections": payload.sections},
    )
    db.commit()
    return report


@router.get("/{project_id}/runs/{run_id}/audit-events", response_model=list[AuditEventRead])
def list_run_audit_events(
    project_id: int,
    run_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: AuthenticatedUser,
) -> list[AuditEvent]:
    get_project_or_404(db, project_id)
    get_run_or_404(db, project_id, run_id)
    return list(
        db.scalars(
            select(AuditEvent)
            .where(AuditEvent.project_id == project_id, AuditEvent.evaluation_run_id == run_id)
            .order_by(AuditEvent.created_at.desc(), AuditEvent.id.desc())
        ).all()
    )


@router.get("/{project_id}/runs/{run_id}/background-jobs", response_model=list[BackgroundJobRead])
def list_run_background_jobs(
    project_id: int,
    run_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: AuthenticatedUser,
) -> list[BackgroundJob]:
    get_project_or_404(db, project_id)
    get_run_or_404(db, project_id, run_id)
    return list(
        db.scalars(
            select(BackgroundJob)
            .where(BackgroundJob.project_id == project_id, BackgroundJob.evaluation_run_id == run_id)
            .order_by(BackgroundJob.created_at.desc(), BackgroundJob.id.desc())
        ).all()
    )


@router.post(
    "/{project_id}/runs/{run_id}/background-jobs/rag-execution",
    response_model=BackgroundJobRead,
    status_code=status.HTTP_202_ACCEPTED,
)
def queue_rag_execution_job(
    project_id: int,
    run_id: int,
    payload: RagExecutionRequest,
    background_tasks: BackgroundTasks,
    db: Annotated[Session, Depends(get_db)],
    current_user: WritableUser,
) -> BackgroundJob:
    get_project_or_404(db, project_id)
    get_run_or_404(db, project_id, run_id)
    job = create_background_job(
        db,
        current_user,
        job_type="rag_execution",
        project_id=project_id,
        run_id=run_id,
        input_payload=payload.model_dump(),
    )
    db.commit()
    db.refresh(job)
    background_tasks.add_task(process_background_job, job.id)
    return job


@router.post(
    "/{project_id}/runs/{run_id}/background-jobs/auto-evaluation",
    response_model=BackgroundJobRead,
    status_code=status.HTTP_202_ACCEPTED,
)
def queue_auto_evaluation_job(
    project_id: int,
    run_id: int,
    background_tasks: BackgroundTasks,
    db: Annotated[Session, Depends(get_db)],
    current_user: WritableUser,
) -> BackgroundJob:
    get_project_or_404(db, project_id)
    get_run_or_404(db, project_id, run_id)
    job = create_background_job(
        db,
        current_user,
        job_type="automated_evaluation",
        project_id=project_id,
        run_id=run_id,
    )
    db.commit()
    db.refresh(job)
    background_tasks.add_task(process_background_job, job.id)
    return job


@router.post(
    "/{project_id}/runs/{run_id}/background-jobs/report",
    response_model=BackgroundJobRead,
    status_code=status.HTTP_202_ACCEPTED,
)
def queue_report_job(
    project_id: int,
    run_id: int,
    payload: ReportBuilderRequest,
    background_tasks: BackgroundTasks,
    db: Annotated[Session, Depends(get_db)],
    current_user: AuthenticatedUser,
) -> BackgroundJob:
    get_project_or_404(db, project_id)
    get_run_or_404(db, project_id, run_id)
    job = create_background_job(
        db,
        current_user,
        job_type="report_builder",
        project_id=project_id,
        run_id=run_id,
        input_payload=payload.model_dump(),
    )
    db.commit()
    db.refresh(job)
    background_tasks.add_task(process_background_job, job.id)
    return job


@router.get("/{project_id}/runs/{run_id}/errors", response_model=list[ErrorAnnotationRead])
def list_error_annotations(
    project_id: int,
    run_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: AuthenticatedUser,
) -> list[ErrorAnnotation]:
    get_project_or_404(db, project_id)
    get_run_or_404(db, project_id, run_id)
    return list(
        db.scalars(
            select(ErrorAnnotation)
            .where(ErrorAnnotation.evaluation_run_id == run_id)
            .order_by(ErrorAnnotation.created_at.desc(), ErrorAnnotation.id.desc())
        ).all()
    )


@router.get("/{project_id}/runs/{run_id}/export.json")
def export_run_json(
    project_id: int,
    run_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: AuthenticatedUser,
) -> dict[str, object]:
    project = get_project_or_404(db, project_id)
    run = get_run_or_404(db, project_id, run_id)
    return build_run_summary(db, project, run)


@router.get("/{project_id}/runs/{run_id}/export.csv")
def export_run_csv(
    project_id: int,
    run_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: AuthenticatedUser,
) -> StreamingResponse:
    project = get_project_or_404(db, project_id)
    run = get_run_or_404(db, project_id, run_id)
    summary = build_run_summary(db, project, run)
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "question_id",
            "question_text",
            "answer_id",
            "answer_text",
            "reviewed",
            "overall_score",
            "citation_quality_score",
            "latency_cost_score",
            "evidence_faithfulness_score",
            "answer_relevance_score",
            "retrieval_quality_score",
            "evaluation_mode",
            "judge_model_name",
            "expected_source_match",
            "first_relevant_rank",
            "retrieved_chunk_count",
            "precision_at_k",
            "recall_at_k",
            "reciprocal_rank",
            "missing_evidence",
        ]
    )
    for row in summary["question_results"]:
        writer.writerow(
            [
                row["question_id"],
                row["question_text"],
                row["answer_id"],
                row["answer_text"],
                row["reviewed"],
                row["overall_score"],
                row["citation_quality_score"],
                row["latency_cost_score"],
                row["evidence_faithfulness_score"],
                row["answer_relevance_score"],
                row["retrieval_quality_score"],
                row["evaluation_mode"],
                row["judge_model_name"],
                row["expected_source_match"],
                row["first_relevant_rank"],
                row["retrieved_chunk_count"],
                row["precision_at_k"],
                row["recall_at_k"],
                row["reciprocal_rank"],
                row["missing_evidence"],
            ]
        )

    filename = f"clear-rag-run-{run_id}-summary.csv"
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.patch("/{project_id}/runs/{run_id}", response_model=EvaluationRunRead)
def update_run(
    project_id: int,
    run_id: int,
    payload: EvaluationRunUpdate,
    db: Annotated[Session, Depends(get_db)],
    _: WritableUser,
) -> EvaluationRun:
    get_project_or_404(db, project_id)
    run = get_run_or_404(db, project_id, run_id)
    apply_updates(run, payload)
    db.commit()
    db.refresh(run)
    return run


@router.delete("/{project_id}/runs/{run_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_run(
    project_id: int,
    run_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: WritableUser,
) -> Response:
    get_project_or_404(db, project_id)
    run = get_run_or_404(db, project_id, run_id)
    db.delete(run)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{project_id}/runs/{run_id}/execute", response_model=RagExecutionRead)
def execute_run(
    project_id: int,
    run_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: WritableUser,
    payload: RagExecutionRequest | None = None,
) -> dict[str, object]:
    get_project_or_404(db, project_id)
    run = get_run_or_404(db, project_id, run_id)
    retrieval_mode = payload.retrieval_mode if payload else "keyword"
    try:
        result = execute_rag_run(db, run, get_settings(), retrieval_mode=retrieval_mode)
    except RagExecutionError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    create_audit_event(
        db,
        current_user,
        event_type="rag_executed",
        entity_type="evaluation_run",
        entity_id=run.id,
        project_id=project_id,
        run_id=run.id,
        event_summary=f"Gemini RAG was executed for run '{run.name}'.",
        metadata={
            "status": result.status,
            "model_name": result.model_name,
            "processed_questions": result.processed_questions,
            "retrieved_chunks_created": result.retrieved_chunks_created,
            "generated_answers_created": result.generated_answers_created,
            "retrieval_mode": result.retrieval_mode,
        },
    )
    db.commit()
    return {
        "run_id": result.run_id,
        "status": result.status,
        "model_name": result.model_name,
        "processed_questions": result.processed_questions,
        "retrieved_chunks_created": result.retrieved_chunks_created,
        "generated_answers_created": result.generated_answers_created,
        "retrieval_mode": result.retrieval_mode,
        "message": result.message,
    }


def run_automated_clear_rag_evaluation(
    db: Session,
    project_id: int,
    run: EvaluationRun,
    current_user: User,
) -> dict[str, object]:
    answers = list(
        db.scalars(
            select(GeneratedAnswer)
            .where(GeneratedAnswer.evaluation_run_id == run.id)
            .order_by(GeneratedAnswer.created_at.asc(), GeneratedAnswer.id.asc())
        ).all()
    )
    if not answers:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Run Gemini RAG or add generated answers before automated evaluation.",
        )

    questions = {
        question.id: question
        for question in db.scalars(select(TestQuestion).where(TestQuestion.project_id == project_id)).all()
    }
    chunks_by_question: dict[int, list[RetrievedChunk]] = {}
    for chunk in db.scalars(
        select(RetrievedChunk)
        .where(RetrievedChunk.evaluation_run_id == run.id)
        .order_by(RetrievedChunk.test_question_id.asc(), RetrievedChunk.rank.asc(), RetrievedChunk.id.asc())
    ).all():
        chunks_by_question.setdefault(chunk.test_question_id, []).append(chunk)

    settings = get_settings()
    client = GeminiClient(settings)
    db.execute(
        delete(EvaluationRecord).where(
            EvaluationRecord.evaluation_run_id == run.id,
            EvaluationRecord.evaluation_mode == "automated",
        )
    )

    evaluated_answers = 0
    skipped_answers = 0
    judge_model_name = settings.default_llm_model
    try:
        for answer in answers:
            question = questions.get(answer.test_question_id)
            if question is None:
                skipped_answers += 1
                continue

            judgment = judge_clear_rag_answer(
                question=question,
                answer=answer,
                chunks=chunks_by_question.get(question.id, []),
                client=client,
            )
            judge_model_name = judgment.judge_model_name
            evaluation = EvaluationRecord(
                evaluation_run_id=run.id,
                test_question_id=question.id,
                generated_answer_id=answer.id,
                reviewer_user_id=current_user.id,
                citation_quality_score=judgment.citation_quality_score,
                latency_cost_score=judgment.latency_cost_score,
                evidence_faithfulness_score=judgment.evidence_faithfulness_score,
                answer_relevance_score=judgment.answer_relevance_score,
                retrieval_quality_score=judgment.retrieval_quality_score,
                overall_score=Decimal("1.00"),
                reviewer_notes=judgment.reviewer_notes,
                suggested_improvement=judgment.suggested_improvement,
                evaluation_mode="automated",
                judge_model_name=judgment.judge_model_name,
                judge_reasoning=judgment.judge_reasoning,
                review_status="pending_review",
            )
            evaluation.overall_score = calculate_overall_score(evaluation)
            db.add(evaluation)
            evaluated_answers += 1
        run.judge_model_name = judge_model_name
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    create_audit_event(
        db,
        current_user,
        event_type="automated_evaluation_completed",
        entity_type="evaluation_run",
        entity_id=run.id,
        project_id=project_id,
        run_id=run.id,
        event_summary=f"Automated CLEAR-RAG evaluation completed for run '{run.name}'.",
        metadata={
            "evaluated_answers": evaluated_answers,
            "skipped_answers": skipped_answers,
            "judge_model_name": judge_model_name,
        },
    )
    db.commit()
    return {
        "run_id": run.id,
        "evaluated_answers": evaluated_answers,
        "skipped_answers": skipped_answers,
        "judge_model_name": judge_model_name,
        "message": "Automated CLEAR-RAG evaluation completed.",
    }


@router.post("/{project_id}/runs/{run_id}/auto-evaluate", response_model=AutoEvaluationRunRead)
def auto_evaluate_run(
    project_id: int,
    run_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: WritableUser,
) -> dict[str, object]:
    get_project_or_404(db, project_id)
    run = get_run_or_404(db, project_id, run_id)
    return run_automated_clear_rag_evaluation(db, project_id, run, current_user)


@router.post(
    "/{project_id}/runs/{run_id}/questions/{question_id}/retrieved-chunks",
    response_model=RetrievedChunkRead,
    status_code=status.HTTP_201_CREATED,
)
def create_retrieved_chunk(
    project_id: int,
    run_id: int,
    question_id: int,
    payload: RetrievedChunkCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: WritableUser,
) -> RetrievedChunk:
    validate_output_scope(db, project_id, run_id, question_id, payload.source_document_id)
    chunk = RetrievedChunk(
        **payload.model_dump(),
        evaluation_run_id=run_id,
        test_question_id=question_id,
    )
    db.add(chunk)
    db.flush()
    create_audit_event(
        db,
        current_user,
        event_type="retrieved_chunk_added",
        entity_type="retrieved_chunk",
        entity_id=chunk.id,
        project_id=project_id,
        run_id=run_id,
        question_id=question_id,
        event_summary=f"Retrieved chunk rank {chunk.rank} was added.",
        metadata={"source_document_id": chunk.source_document_id, "relevance_label": chunk.relevance_label},
    )
    db.commit()
    db.refresh(chunk)
    return chunk


@router.get(
    "/{project_id}/runs/{run_id}/questions/{question_id}/retrieved-chunks",
    response_model=list[RetrievedChunkRead],
)
def list_retrieved_chunks(
    project_id: int,
    run_id: int,
    question_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: AuthenticatedUser,
) -> list[RetrievedChunk]:
    validate_output_scope(db, project_id, run_id, question_id)
    return list(
        db.scalars(
            select(RetrievedChunk)
            .where(
                RetrievedChunk.evaluation_run_id == run_id,
                RetrievedChunk.test_question_id == question_id,
            )
            .order_by(RetrievedChunk.rank.asc(), RetrievedChunk.id.asc())
        ).all()
    )


@router.delete(
    "/{project_id}/runs/{run_id}/questions/{question_id}/retrieved-chunks/{chunk_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_retrieved_chunk(
    project_id: int,
    run_id: int,
    question_id: int,
    chunk_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: WritableUser,
) -> Response:
    validate_output_scope(db, project_id, run_id, question_id)
    chunk = get_chunk_or_404(db, run_id, question_id, chunk_id)
    db.delete(chunk)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{project_id}/runs/{run_id}/questions/{question_id}/generated-answers",
    response_model=GeneratedAnswerRead,
    status_code=status.HTTP_201_CREATED,
)
def create_generated_answer(
    project_id: int,
    run_id: int,
    question_id: int,
    payload: GeneratedAnswerCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: WritableUser,
) -> GeneratedAnswer:
    validate_output_scope(db, project_id, run_id, question_id)
    answer = GeneratedAnswer(
        **payload.model_dump(),
        evaluation_run_id=run_id,
        test_question_id=question_id,
    )
    db.add(answer)
    db.flush()
    create_audit_event(
        db,
        current_user,
        event_type="generated_answer_added",
        entity_type="generated_answer",
        entity_id=answer.id,
        project_id=project_id,
        run_id=run_id,
        question_id=question_id,
        answer_id=answer.id,
        event_summary="A generated answer was added.",
        metadata={"model_name": answer.model_name, "input_tokens": answer.input_tokens, "output_tokens": answer.output_tokens},
    )
    db.commit()
    db.refresh(answer)
    return answer


@router.get(
    "/{project_id}/runs/{run_id}/questions/{question_id}/generated-answers",
    response_model=list[GeneratedAnswerRead],
)
def list_generated_answers(
    project_id: int,
    run_id: int,
    question_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: AuthenticatedUser,
) -> list[GeneratedAnswer]:
    validate_output_scope(db, project_id, run_id, question_id)
    return list(
        db.scalars(
            select(GeneratedAnswer)
            .where(
                GeneratedAnswer.evaluation_run_id == run_id,
                GeneratedAnswer.test_question_id == question_id,
            )
            .order_by(GeneratedAnswer.created_at.desc(), GeneratedAnswer.id.desc())
        ).all()
    )


@router.delete(
    "/{project_id}/runs/{run_id}/questions/{question_id}/generated-answers/{answer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_generated_answer(
    project_id: int,
    run_id: int,
    question_id: int,
    answer_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: WritableUser,
) -> Response:
    validate_output_scope(db, project_id, run_id, question_id)
    answer = get_answer_or_404(db, run_id, question_id, answer_id)
    db.delete(answer)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{project_id}/runs/{run_id}/questions/{question_id}/answers/{answer_id}/evaluations",
    response_model=EvaluationRecordRead,
    status_code=status.HTTP_201_CREATED,
)
def create_evaluation_record(
    project_id: int,
    run_id: int,
    question_id: int,
    answer_id: int,
    payload: EvaluationRecordCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: WritableUser,
) -> EvaluationRecord:
    validate_output_scope(db, project_id, run_id, question_id)
    get_answer_or_404(db, run_id, question_id, answer_id)
    evaluation = EvaluationRecord(
        **payload.model_dump(),
        evaluation_run_id=run_id,
        test_question_id=question_id,
        generated_answer_id=answer_id,
        reviewer_user_id=current_user.id,
        overall_score=Decimal("1.00"),
        evaluation_mode="human",
        review_status="approved",
        reviewed_by_user_id=current_user.id,
        reviewed_at=datetime.now(timezone.utc),
    )
    evaluation.overall_score = calculate_overall_score(evaluation)
    db.add(evaluation)
    db.flush()
    create_audit_event(
        db,
        current_user,
        event_type="human_evaluation_created",
        entity_type="evaluation_record",
        entity_id=evaluation.id,
        project_id=project_id,
        run_id=run_id,
        question_id=question_id,
        answer_id=answer_id,
        evaluation_record_id=evaluation.id,
        event_summary="A human evaluation was recorded.",
        metadata={
            "overall_score": evaluation.overall_score,
            "review_status": evaluation.review_status,
            "evaluation_mode": evaluation.evaluation_mode,
        },
    )
    db.commit()
    db.refresh(evaluation)
    return evaluation


@router.post(
    "/{project_id}/runs/{run_id}/questions/{question_id}/answers/{answer_id}/errors",
    response_model=ErrorAnnotationRead,
    status_code=status.HTTP_201_CREATED,
)
def create_error_annotation(
    project_id: int,
    run_id: int,
    question_id: int,
    answer_id: int,
    payload: ErrorAnnotationCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: WritableUser,
) -> ErrorAnnotation:
    validate_output_scope(db, project_id, run_id, question_id)
    get_answer_or_404(db, run_id, question_id, answer_id)
    validate_error_evaluation_scope(db, run_id, question_id, answer_id, payload.evaluation_record_id)
    annotation = ErrorAnnotation(
        evaluation_run_id=run_id,
        test_question_id=question_id,
        generated_answer_id=answer_id,
        evaluation_record_id=payload.evaluation_record_id,
        created_by_user_id=current_user.id,
        category=payload.category,
        severity=payload.severity,
        source="human",
        notes=payload.notes,
        evidence_reference=payload.evidence_reference,
    )
    db.add(annotation)
    db.flush()
    create_audit_event(
        db,
        current_user,
        event_type="error_tag_created",
        entity_type="error_annotation",
        entity_id=annotation.id,
        project_id=project_id,
        run_id=run_id,
        question_id=question_id,
        answer_id=answer_id,
        evaluation_record_id=annotation.evaluation_record_id,
        event_summary=f"Error tag '{annotation.category}' was added.",
        metadata={"category": annotation.category, "severity": annotation.severity, "source": annotation.source},
    )
    db.commit()
    db.refresh(annotation)
    return annotation


@router.get(
    "/{project_id}/runs/{run_id}/evaluations",
    response_model=list[EvaluationRecordRead],
)
def list_evaluation_records(
    project_id: int,
    run_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: AuthenticatedUser,
) -> list[EvaluationRecord]:
    get_project_or_404(db, project_id)
    get_run_or_404(db, project_id, run_id)
    return list(
        db.scalars(
            select(EvaluationRecord)
            .where(EvaluationRecord.evaluation_run_id == run_id)
            .order_by(EvaluationRecord.created_at.desc(), EvaluationRecord.id.desc())
        ).all()
    )


@router.patch(
    "/{project_id}/runs/{run_id}/evaluations/{evaluation_id}",
    response_model=EvaluationRecordRead,
)
def update_evaluation_record(
    project_id: int,
    run_id: int,
    evaluation_id: int,
    payload: EvaluationRecordUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: WritableUser,
) -> EvaluationRecord:
    get_project_or_404(db, project_id)
    get_run_or_404(db, project_id, run_id)
    evaluation = get_evaluation_or_404(db, run_id, evaluation_id)
    apply_updates(evaluation, payload)
    evaluation.overall_score = calculate_overall_score(evaluation)
    create_audit_event(
        db,
        current_user,
        event_type="evaluation_updated",
        entity_type="evaluation_record",
        entity_id=evaluation.id,
        project_id=project_id,
        run_id=run_id,
        question_id=evaluation.test_question_id,
        answer_id=evaluation.generated_answer_id,
        evaluation_record_id=evaluation.id,
        event_summary="An evaluation record was updated.",
        metadata=payload.model_dump(exclude_unset=True),
    )
    db.commit()
    db.refresh(evaluation)
    return evaluation


@router.patch(
    "/{project_id}/runs/{run_id}/errors/{error_id}",
    response_model=ErrorAnnotationRead,
)
def update_error_annotation(
    project_id: int,
    run_id: int,
    error_id: int,
    payload: ErrorAnnotationUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: WritableUser,
) -> ErrorAnnotation:
    get_project_or_404(db, project_id)
    get_run_or_404(db, project_id, run_id)
    annotation = get_error_annotation_or_404(db, run_id, error_id)
    apply_updates(annotation, payload)
    create_audit_event(
        db,
        current_user,
        event_type="error_tag_updated",
        entity_type="error_annotation",
        entity_id=annotation.id,
        project_id=project_id,
        run_id=run_id,
        question_id=annotation.test_question_id,
        answer_id=annotation.generated_answer_id,
        evaluation_record_id=annotation.evaluation_record_id,
        event_summary=f"Error tag '{annotation.category}' was updated.",
        metadata=payload.model_dump(exclude_unset=True),
    )
    db.commit()
    db.refresh(annotation)
    return annotation


@router.patch(
    "/{project_id}/runs/{run_id}/evaluations/{evaluation_id}/review",
    response_model=EvaluationRecordRead,
)
def review_evaluation_record(
    project_id: int,
    run_id: int,
    evaluation_id: int,
    payload: EvaluationReviewUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: WritableUser,
) -> EvaluationRecord:
    get_project_or_404(db, project_id)
    get_run_or_404(db, project_id, run_id)
    evaluation = get_evaluation_or_404(db, run_id, evaluation_id)
    score_fields = [
        "citation_quality_score",
        "latency_cost_score",
        "evidence_faithfulness_score",
        "answer_relevance_score",
        "retrieval_quality_score",
    ]
    requested_score_changes = {
        field_name: getattr(payload, field_name)
        for field_name in score_fields
        if getattr(payload, field_name) is not None and getattr(payload, field_name) != getattr(evaluation, field_name)
    }
    if requested_score_changes and not payload.score_change_reason:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="score_change_reason is required when changing scores.",
        )

    for field_name in score_fields:
        if field_name in requested_score_changes:
            setattr(evaluation, field_name, requested_score_changes[field_name])

    if requested_score_changes:
        evaluation.overall_score = calculate_overall_score(evaluation)
        evaluation.evaluation_mode = "human"

    evaluation.review_status = payload.review_status
    evaluation.review_notes = payload.review_notes
    evaluation.score_change_reason = payload.score_change_reason
    if payload.reviewer_notes is not None:
        evaluation.reviewer_notes = payload.reviewer_notes
    if payload.suggested_improvement is not None:
        evaluation.suggested_improvement = payload.suggested_improvement
    evaluation.reviewed_by_user_id = current_user.id
    evaluation.reviewed_at = datetime.now(timezone.utc)
    create_audit_event(
        db,
        current_user,
        event_type="evaluation_reviewed",
        entity_type="evaluation_record",
        entity_id=evaluation.id,
        project_id=project_id,
        run_id=run_id,
        question_id=evaluation.test_question_id,
        answer_id=evaluation.generated_answer_id,
        evaluation_record_id=evaluation.id,
        event_summary=f"Evaluation review status changed to '{evaluation.review_status}'.",
        metadata={
            "review_status": evaluation.review_status,
            "score_changed": bool(requested_score_changes),
            "score_change_reason": evaluation.score_change_reason,
        },
    )
    db.commit()
    db.refresh(evaluation)
    return evaluation


@router.delete(
    "/{project_id}/runs/{run_id}/evaluations/{evaluation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_evaluation_record(
    project_id: int,
    run_id: int,
    evaluation_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: WritableUser,
) -> Response:
    get_project_or_404(db, project_id)
    get_run_or_404(db, project_id, run_id)
    evaluation = get_evaluation_or_404(db, run_id, evaluation_id)
    db.delete(evaluation)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/{project_id}/runs/{run_id}/errors/{error_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_error_annotation(
    project_id: int,
    run_id: int,
    error_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: WritableUser,
) -> Response:
    get_project_or_404(db, project_id)
    get_run_or_404(db, project_id, run_id)
    annotation = get_error_annotation_or_404(db, run_id, error_id)
    create_audit_event(
        db,
        current_user,
        event_type="error_tag_deleted",
        entity_type="error_annotation",
        entity_id=annotation.id,
        project_id=project_id,
        run_id=run_id,
        question_id=annotation.test_question_id,
        answer_id=annotation.generated_answer_id,
        evaluation_record_id=annotation.evaluation_record_id,
        event_summary=f"Error tag '{annotation.category}' was deleted.",
        metadata={"category": annotation.category, "severity": annotation.severity},
    )
    db.delete(annotation)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
