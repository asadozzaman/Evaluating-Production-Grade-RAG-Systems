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
    question_datasets: Mapped[list["QuestionDataset"]] = relationship(
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
    document_chunks: Mapped[list["DocumentChunk"]] = relationship(
        back_populates="source_document",
        cascade="all, delete-orphan",
    )


class DocumentChunk(TimestampMixin, Base):
    __tablename__ = "document_chunks"
    __table_args__ = (
        CheckConstraint("chunk_index > 0", name="ck_document_chunks_chunk_index_positive"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source_document_id: Mapped[int] = mapped_column(
        ForeignKey("source_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    section_reference: Mapped[str | None] = mapped_column(String(255))
    embedding_model: Mapped[str] = mapped_column(String(120), nullable=False)
    embedding_json: Mapped[str] = mapped_column(Text, nullable=False)

    source_document: Mapped[SourceDocument] = relationship(back_populates="document_chunks")


class QuestionDataset(TimestampMixin, Base):
    __tablename__ = "question_datasets"
    __table_args__ = (
        CheckConstraint("question_count >= 0", name="ck_question_datasets_question_count_non_negative"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    dataset_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    dataset_version: Mapped[str | None] = mapped_column(String(80))
    imported_file_name: Mapped[str | None] = mapped_column(String(255))
    question_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)

    project: Mapped[Project] = relationship(back_populates="question_datasets")
    created_by: Mapped[User] = relationship(foreign_keys=[created_by_user_id])
    test_questions: Mapped[list["TestQuestion"]] = relationship(back_populates="dataset")


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
    dataset_id: Mapped[int | None] = mapped_column(ForeignKey("question_datasets.id", ondelete="SET NULL"), index=True)
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)

    project: Mapped[Project] = relationship(back_populates="test_questions")
    dataset: Mapped[QuestionDataset | None] = relationship(back_populates="test_questions")
    created_by: Mapped[User] = relationship(foreign_keys=[created_by_user_id])
    retrieved_chunks: Mapped[list["RetrievedChunk"]] = relationship(back_populates="test_question")
    generated_answers: Mapped[list["GeneratedAnswer"]] = relationship(back_populates="test_question")
    evaluation_records: Mapped[list["EvaluationRecord"]] = relationship(back_populates="test_question")
    error_annotations: Mapped[list["ErrorAnnotation"]] = relationship(back_populates="test_question")


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
    dataset_id: Mapped[int | None] = mapped_column(ForeignKey("question_datasets.id", ondelete="SET NULL"), index=True)
    batch_document_ids: Mapped[str | None] = mapped_column(Text)
    auto_evaluate_enabled: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    batch_status: Mapped[str | None] = mapped_column(String(30))
    current_step: Mapped[str | None] = mapped_column(String(80))
    completed_steps: Mapped[str | None] = mapped_column(Text)
    failed_step: Mapped[str | None] = mapped_column(String(80))
    batch_error_message: Mapped[str | None] = mapped_column(Text)
    batch_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    batch_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    retrieval_mode: Mapped[str | None] = mapped_column(String(30))
    generator_model_name: Mapped[str | None] = mapped_column(String(120))
    embedding_model_name: Mapped[str | None] = mapped_column(String(120))
    judge_model_name: Mapped[str | None] = mapped_column(String(120))
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    project: Mapped[Project] = relationship(back_populates="evaluation_runs")
    dataset: Mapped[QuestionDataset | None] = relationship()
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
    error_annotations: Mapped[list["ErrorAnnotation"]] = relationship(
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
    error_annotations: Mapped[list["ErrorAnnotation"]] = relationship(back_populates="generated_answer")


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
        CheckConstraint("evaluation_mode IN ('human', 'automated')", name="ck_evaluation_records_evaluation_mode"),
        CheckConstraint(
            "review_status IN ('pending_review', 'approved', 'needs_revision')",
            name="ck_evaluation_records_review_status",
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
    evaluation_mode: Mapped[str] = mapped_column(String(30), default="human", server_default="human", nullable=False)
    judge_model_name: Mapped[str | None] = mapped_column(String(120))
    judge_reasoning: Mapped[str | None] = mapped_column(Text)
    review_status: Mapped[str] = mapped_column(String(30), default="pending_review", server_default="pending_review", nullable=False)
    reviewed_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    review_notes: Mapped[str | None] = mapped_column(Text)
    score_change_reason: Mapped[str | None] = mapped_column(Text)

    evaluation_run: Mapped[EvaluationRun] = relationship(back_populates="evaluation_records")
    test_question: Mapped[TestQuestion] = relationship(back_populates="evaluation_records")
    generated_answer: Mapped[GeneratedAnswer] = relationship(back_populates="evaluation_records")
    reviewer: Mapped[User] = relationship(foreign_keys=[reviewer_user_id])
    reviewed_by: Mapped[User | None] = relationship(foreign_keys=[reviewed_by_user_id])
    error_annotations: Mapped[list["ErrorAnnotation"]] = relationship(back_populates="evaluation_record")


class ErrorAnnotation(TimestampMixin, Base):
    __tablename__ = "error_annotations"
    __table_args__ = (
        CheckConstraint(
            "category IN ('retrieval_miss', 'citation_error', 'hallucination', 'incomplete_answer', 'irrelevant_answer', 'contradiction', 'latency_cost', 'format_error', 'policy_ambiguity', 'other')",
            name="ck_error_annotations_category",
        ),
        CheckConstraint(
            "severity IN ('low', 'medium', 'high', 'critical')",
            name="ck_error_annotations_severity",
        ),
        CheckConstraint(
            "source IN ('human', 'automated')",
            name="ck_error_annotations_source",
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
    generated_answer_id: Mapped[int] = mapped_column(
        ForeignKey("generated_answers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    evaluation_record_id: Mapped[int | None] = mapped_column(
        ForeignKey("evaluation_records.id", ondelete="SET NULL"),
        index=True,
    )
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(40), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    source: Mapped[str] = mapped_column(String(20), default="human", server_default="human", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    evidence_reference: Mapped[str | None] = mapped_column(Text)

    evaluation_run: Mapped[EvaluationRun] = relationship(back_populates="error_annotations")
    test_question: Mapped[TestQuestion] = relationship(back_populates="error_annotations")
    generated_answer: Mapped[GeneratedAnswer] = relationship(back_populates="error_annotations")
    evaluation_record: Mapped[EvaluationRecord | None] = relationship(back_populates="error_annotations")
    created_by: Mapped[User] = relationship(foreign_keys=[created_by_user_id])


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    actor_user_id: Mapped[int | None] = mapped_column(Integer, index=True)
    project_id: Mapped[int | None] = mapped_column(Integer, index=True)
    evaluation_run_id: Mapped[int | None] = mapped_column(Integer, index=True)
    test_question_id: Mapped[int | None] = mapped_column(Integer, index=True)
    generated_answer_id: Mapped[int | None] = mapped_column(Integer, index=True)
    evaluation_record_id: Mapped[int | None] = mapped_column(Integer, index=True)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    entity_id: Mapped[int | None] = mapped_column(Integer, index=True)
    event_summary: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
        index=True,
    )


class BackgroundJob(Base):
    __tablename__ = "background_jobs"
    __table_args__ = (
        CheckConstraint("status IN ('queued', 'running', 'completed', 'failed')", name="ck_background_jobs_status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    job_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), default="queued", server_default="queued", nullable=False, index=True)
    project_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    evaluation_run_id: Mapped[int | None] = mapped_column(Integer, index=True)
    requested_by_user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    current_step: Mapped[str | None] = mapped_column(String(120))
    input_json: Mapped[str | None] = mapped_column(Text)
    result_json: Mapped[str | None] = mapped_column(Text)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
