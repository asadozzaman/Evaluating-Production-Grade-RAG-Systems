from collections.abc import Generator
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import (
    EvaluationRecord,
    EvaluationRun,
    GeneratedAnswer,
    Project,
    RetrievedChunk,
    Role,
    SourceDocument,
    TestQuestion as QuestionModel,
    User,
)
from app.security import hash_password


@pytest.fixture()
def db_session() -> Generator[Session]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def create_user(db: Session) -> User:
    role = Role(name="admin", description="Admin role")
    user = User(
        email="admin@example.com",
        full_name="Admin User",
        hashed_password=hash_password("StrongPass123!"),
        roles=[role],
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_evaluation_graph(db: Session) -> tuple[Project, QuestionModel, EvaluationRun, GeneratedAnswer]:
    user = create_user(db)
    project = Project(
        name="HR Policy RAG Assistant",
        description="Evaluation workspace for an internal HR assistant.",
        system_type="internal_knowledge_assistant",
        target_users="Employees",
        created_by_user_id=user.id,
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    source_document = SourceDocument(
        project_id=project.id,
        title="HR Leave Policy",
        document_type="policy",
        source_uri="s3://example/hr-leave-policy.pdf",
        version="v1",
    )
    question = QuestionModel(
        project_id=project.id,
        question_text="How many annual leave days does an employee receive after one year?",
        question_type="simple_factual",
        expected_source="HR Leave Policy, Section 1.1",
        created_by_user_id=user.id,
    )
    run = EvaluationRun(
        project_id=project.id,
        name="Baseline Evaluation",
        system_version="v1",
        notes="Basic vector search and simple prompt.",
        created_by_user_id=user.id,
    )
    db.add_all([source_document, question, run])
    db.commit()
    db.refresh(source_document)
    db.refresh(question)
    db.refresh(run)

    chunk = RetrievedChunk(
        evaluation_run_id=run.id,
        test_question_id=question.id,
        source_document_id=source_document.id,
        rank=1,
        chunk_text="Full-time employees are eligible for 20 days of annual leave after one year.",
        section_reference="Section 1.1",
        relevance_label="high",
        retrieval_time_ms=120,
    )
    answer = GeneratedAnswer(
        evaluation_run_id=run.id,
        test_question_id=question.id,
        answer_text="After one year, a full-time employee receives 20 days of annual leave.",
        model_name="test-model",
        input_tokens=900,
        output_tokens=80,
        generation_time_ms=1500,
        estimated_cost=Decimal("0.012500"),
    )
    db.add_all([chunk, answer])
    db.commit()
    db.refresh(answer)

    record = EvaluationRecord(
        evaluation_run_id=run.id,
        test_question_id=question.id,
        generated_answer_id=answer.id,
        reviewer_user_id=user.id,
        citation_quality_score=5,
        latency_cost_score=4,
        evidence_faithfulness_score=5,
        answer_relevance_score=5,
        retrieval_quality_score=4,
        overall_score=Decimal("4.60"),
        reviewer_notes="Strong answer with one extra retrieved chunk.",
        suggested_improvement="Improve retrieval filtering.",
    )
    db.add(record)
    db.commit()
    db.refresh(project)
    db.refresh(question)
    db.refresh(run)
    db.refresh(answer)
    return project, question, run, answer


def test_core_evaluation_graph_persists_relationships(db_session: Session) -> None:
    project, question, run, answer = create_evaluation_graph(db_session)

    assert project.source_documents[0].title == "HR Leave Policy"
    assert project.test_questions[0].question_type == "simple_factual"
    assert project.evaluation_runs[0].name == "Baseline Evaluation"
    assert run.retrieved_chunks[0].rank == 1
    assert run.generated_answers[0].model_name == "test-model"
    assert answer.evaluation_records[0].overall_score == Decimal("4.60")
    assert question.evaluation_records[0].reviewer.email == "admin@example.com"


def test_score_constraints_reject_values_outside_clear_rag_rubric(db_session: Session) -> None:
    _, question, run, answer = create_evaluation_graph(db_session)
    user = answer.evaluation_records[0].reviewer

    invalid_record = EvaluationRecord(
        evaluation_run_id=run.id,
        test_question_id=question.id,
        generated_answer_id=answer.id,
        reviewer_user_id=user.id,
        citation_quality_score=6,
        latency_cost_score=4,
        evidence_faithfulness_score=5,
        answer_relevance_score=5,
        retrieval_quality_score=4,
        overall_score=Decimal("4.80"),
    )
    db_session.add(invalid_record)

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_invalid_question_type_is_rejected(db_session: Session) -> None:
    user = create_user(db_session)
    project = Project(
        name="Support RAG",
        system_type="customer_support",
        target_users="Customers",
        created_by_user_id=user.id,
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    question = QuestionModel(
        project_id=project.id,
        question_text="Can I get a refund?",
        question_type="unsupported_type",
        created_by_user_id=user.id,
    )
    db_session.add(question)

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_retrieval_and_generation_numeric_constraints(db_session: Session) -> None:
    project, question, run, _ = create_evaluation_graph(db_session)
    source_document = project.source_documents[0]

    bad_chunk = RetrievedChunk(
        evaluation_run_id=run.id,
        test_question_id=question.id,
        source_document_id=source_document.id,
        rank=0,
        chunk_text="Bad rank",
    )
    db_session.add(bad_chunk)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()
    bad_answer = GeneratedAnswer(
        evaluation_run_id=run.id,
        test_question_id=question.id,
        answer_text="Bad token count",
        input_tokens=-1,
    )
    db_session.add(bad_answer)

    with pytest.raises(IntegrityError):
        db_session.commit()
