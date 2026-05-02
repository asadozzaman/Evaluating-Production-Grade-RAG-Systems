from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, ForeignKey, Integer, Numeric, String, Table, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    roles: Mapped[list["Role"]] = relationship(
        secondary=user_roles,
        back_populates="users",
        lazy="selectin",
    )


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)

    users: Mapped[list[User]] = relationship(
        secondary=user_roles,
        back_populates="roles",
    )


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )


class Project(TimestampMixin, Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    system_type: Mapped[str] = mapped_column(String(100), nullable=False)
    target_users: Mapped[str] = mapped_column(String(255), nullable=False)
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)

    created_by: Mapped[User] = relationship(foreign_keys=[created_by_user_id])
    source_documents: Mapped[list["SourceDocument"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
    test_questions: Mapped[list["TestQuestion"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
    evaluation_runs: Mapped[list["EvaluationRun"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )


class SourceDocument(TimestampMixin, Base):
    __tablename__ = "source_documents"
    __table_args__ = (
        CheckConstraint("source_kind IN ('uri', 'file')", name="ck_source_documents_source_kind"),
        CheckConstraint(
            "source_kind <> 'uri' OR source_uri IS NOT NULL",
            name="ck_source_documents_uri_requires_source_uri",
        ),
        CheckConstraint(
            "source_kind <> 'file' OR storage_path IS NOT NULL",
            name="ck_source_documents_file_requires_storage_path",
        ),
        CheckConstraint(
            "file_size_bytes IS NULL OR file_size_bytes >= 0",
            name="ck_source_documents_file_size_non_negative",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    document_type: Mapped[str] = mapped_column(String(80), nullable=False)
    source_kind: Mapped[str] = mapped_column(String(20), default="uri", server_default="uri", nullable=False)
    source_uri: Mapped[str | None] = mapped_column(String(500))
    version: Mapped[str | None] = mapped_column(String(80))
    original_file_name: Mapped[str | None] = mapped_column(String(255))
    stored_file_name: Mapped[str | None] = mapped_column(String(255))
    content_type: Mapped[str | None] = mapped_column(String(100))
    file_size_bytes: Mapped[int | None] = mapped_column(Integer)
    storage_path: Mapped[str | None] = mapped_column(String(500))

    project: Mapped[Project] = relationship(back_populates="source_documents")
    retrieved_chunks: Mapped[list["RetrievedChunk"]] = relationship(back_populates="source_document")


class TestQuestion(TimestampMixin, Base):
    __tablename__ = "test_questions"
    __table_args__ = (
        CheckConstraint(
            "question_type IN ('simple_factual', 'conditional', 'multi_document', 'ambiguous', 'edge_case')",
            name="ck_test_questions_question_type",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    expected_source: Mapped[str | None] = mapped_column(String(255))
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)

    project: Mapped[Project] = relationship(back_populates="test_questions")
    created_by: Mapped[User] = relationship(foreign_keys=[created_by_user_id])
    retrieved_chunks: Mapped[list["RetrievedChunk"]] = relationship(back_populates="test_question")
    generated_answers: Mapped[list["GeneratedAnswer"]] = relationship(back_populates="test_question")
    evaluation_records: Mapped[list["EvaluationRecord"]] = relationship(back_populates="test_question")


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'running', 'completed', 'failed')",
            name="ck_evaluation_runs_status",
        ),
        CheckConstraint(
            "processed_question_count >= 0",
            name="ck_evaluation_runs_processed_question_count_non_negative",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    system_version: Mapped[str | None] = mapped_column(String(120))
    notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="pending", server_default="pending", nullable=False)
    last_error: Mapped[str | None] = mapped_column(Text)
    processed_question_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    project: Mapped[Project] = relationship(back_populates="evaluation_runs")
    created_by: Mapped[User] = relationship(foreign_keys=[created_by_user_id])
    retrieved_chunks: Mapped[list["RetrievedChunk"]] = relationship(
        back_populates="evaluation_run",
        cascade="all, delete-orphan",
    )
    generated_answers: Mapped[list["GeneratedAnswer"]] = relationship(
        back_populates="evaluation_run",
        cascade="all, delete-orphan",
    )
    evaluation_records: Mapped[list["EvaluationRecord"]] = relationship(
        back_populates="evaluation_run",
        cascade="all, delete-orphan",
    )


class RetrievedChunk(Base):
    __tablename__ = "retrieved_chunks"
    __table_args__ = (
        CheckConstraint("rank > 0", name="ck_retrieved_chunks_rank_positive"),
        CheckConstraint("retrieval_time_ms IS NULL OR retrieval_time_ms >= 0", name="ck_retrieved_chunks_retrieval_time_non_negative"),
        CheckConstraint(
            "relevance_label IS NULL OR relevance_label IN ('high', 'medium', 'low', 'irrelevant')",
            name="ck_retrieved_chunks_relevance_label",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    evaluation_run_id: Mapped[int] = mapped_column(
        ForeignKey("evaluation_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    test_question_id: Mapped[int] = mapped_column(
        ForeignKey("test_questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_document_id: Mapped[int] = mapped_column(
        ForeignKey("source_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    section_reference: Mapped[str | None] = mapped_column(String(255))
    relevance_label: Mapped[str | None] = mapped_column(String(50))
    retrieval_time_ms: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    evaluation_run: Mapped[EvaluationRun] = relationship(back_populates="retrieved_chunks")
    test_question: Mapped[TestQuestion] = relationship(back_populates="retrieved_chunks")
    source_document: Mapped[SourceDocument] = relationship(back_populates="retrieved_chunks")


class GeneratedAnswer(Base):
    __tablename__ = "generated_answers"
    __table_args__ = (
        CheckConstraint("input_tokens IS NULL OR input_tokens >= 0", name="ck_generated_answers_input_tokens_non_negative"),
        CheckConstraint("output_tokens IS NULL OR output_tokens >= 0", name="ck_generated_answers_output_tokens_non_negative"),
        CheckConstraint(
            "generation_time_ms IS NULL OR generation_time_ms >= 0",
            name="ck_generated_answers_generation_time_non_negative",
        ),
        CheckConstraint("estimated_cost IS NULL OR estimated_cost >= 0", name="ck_generated_answers_estimated_cost_non_negative"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    evaluation_run_id: Mapped[int] = mapped_column(
        ForeignKey("evaluation_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    test_question_id: Mapped[int] = mapped_column(
        ForeignKey("test_questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)
    model_name: Mapped[str | None] = mapped_column(String(120))
    input_tokens: Mapped[int | None] = mapped_column(Integer)
    output_tokens: Mapped[int | None] = mapped_column(Integer)
    generation_time_ms: Mapped[int | None] = mapped_column(Integer)
    estimated_cost: Mapped[Decimal | None] = mapped_column(Numeric(12, 6))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    evaluation_run: Mapped[EvaluationRun] = relationship(back_populates="generated_answers")
    test_question: Mapped[TestQuestion] = relationship(back_populates="generated_answers")
    evaluation_records: Mapped[list["EvaluationRecord"]] = relationship(back_populates="generated_answer")


class EvaluationRecord(TimestampMixin, Base):
    __tablename__ = "evaluation_records"
    __table_args__ = (
        CheckConstraint("citation_quality_score BETWEEN 1 AND 5", name="ck_evaluation_records_citation_quality_score"),
        CheckConstraint("latency_cost_score BETWEEN 1 AND 5", name="ck_evaluation_records_latency_cost_score"),
        CheckConstraint(
            "evidence_faithfulness_score BETWEEN 1 AND 5",
            name="ck_evaluation_records_evidence_faithfulness_score",
        ),
        CheckConstraint("answer_relevance_score BETWEEN 1 AND 5", name="ck_evaluation_records_answer_relevance_score"),
        CheckConstraint("retrieval_quality_score BETWEEN 1 AND 5", name="ck_evaluation_records_retrieval_quality_score"),
        CheckConstraint("overall_score BETWEEN 1 AND 5", name="ck_evaluation_records_overall_score"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    evaluation_run_id: Mapped[int] = mapped_column(
        ForeignKey("evaluation_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    test_question_id: Mapped[int] = mapped_column(
        ForeignKey("test_questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    generated_answer_id: Mapped[int] = mapped_column(
        ForeignKey("generated_answers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    reviewer_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    citation_quality_score: Mapped[int] = mapped_column(Integer, nullable=False)
    latency_cost_score: Mapped[int] = mapped_column(Integer, nullable=False)
    evidence_faithfulness_score: Mapped[int] = mapped_column(Integer, nullable=False)
    answer_relevance_score: Mapped[int] = mapped_column(Integer, nullable=False)
    retrieval_quality_score: Mapped[int] = mapped_column(Integer, nullable=False)
    overall_score: Mapped[Decimal] = mapped_column(Numeric(3, 2), nullable=False)
    reviewer_notes: Mapped[str | None] = mapped_column(Text)
    suggested_improvement: Mapped[str | None] = mapped_column(Text)

    evaluation_run: Mapped[EvaluationRun] = relationship(back_populates="evaluation_records")
    test_question: Mapped[TestQuestion] = relationship(back_populates="evaluation_records")
    generated_answer: Mapped[GeneratedAnswer] = relationship(back_populates="evaluation_records")
    reviewer: Mapped[User] = relationship(foreign_keys=[reviewer_user_id])
