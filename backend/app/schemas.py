from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class RoleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    description: str


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    is_active: bool
    roles: list[RoleRead]


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


class MessageResponse(BaseModel):
    message: str


QuestionType = Literal["simple_factual", "conditional", "multi_document", "ambiguous", "edge_case"]
SourceKind = Literal["uri", "file"]
RelevanceLabel = Literal["high", "medium", "low", "irrelevant"]
RetrievalMode = Literal["keyword", "vector"]
EvaluationMode = Literal["human", "automated"]
ReviewStatus = Literal["pending_review", "approved", "needs_revision"]


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    system_type: str = Field(min_length=1, max_length=100)
    target_users: str = Field(min_length=1, max_length=255)


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    system_type: str | None = Field(default=None, min_length=1, max_length=100)
    target_users: str | None = Field(default=None, min_length=1, max_length=255)


class ProjectRead(ProjectCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_by_user_id: int
    created_at: datetime
    updated_at: datetime


class SourceDocumentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    document_type: str = Field(min_length=1, max_length=80)
    source_kind: SourceKind = "uri"
    source_uri: str | None = Field(default=None, max_length=500)
    version: str | None = Field(default=None, max_length=80)

    @model_validator(mode="after")
    def validate_source(self) -> "SourceDocumentCreate":
        if self.source_kind == "uri" and not self.source_uri:
            raise ValueError("source_uri is required when source_kind is uri")
        if self.source_kind == "file":
            raise ValueError("Use the upload endpoint when source_kind is file")
        return self


class SourceDocumentUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    document_type: str | None = Field(default=None, min_length=1, max_length=80)
    source_uri: str | None = Field(default=None, max_length=500)
    version: str | None = Field(default=None, max_length=80)


class SourceDocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    title: str
    document_type: str
    source_kind: SourceKind
    source_uri: str | None
    version: str | None
    original_file_name: str | None
    stored_file_name: str | None
    content_type: str | None
    file_size_bytes: int | None
    storage_path: str | None
    created_at: datetime
    updated_at: datetime


class DocumentChunkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_document_id: int
    chunk_index: int
    chunk_text: str
    section_reference: str | None
    embedding_model: str
    created_at: datetime
    updated_at: datetime


class DocumentIndexRead(BaseModel):
    document_id: int
    chunks_indexed: int
    embedding_model: str
    message: str


class TestQuestionCreate(BaseModel):
    question_text: str = Field(min_length=1)
    question_type: QuestionType
    expected_source: str | None = Field(default=None, max_length=255)


class TestQuestionUpdate(BaseModel):
    question_text: str | None = Field(default=None, min_length=1)
    question_type: QuestionType | None = None
    expected_source: str | None = Field(default=None, max_length=255)


class TestQuestionRead(TestQuestionCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    dataset_id: int | None
    created_by_user_id: int
    created_at: datetime
    updated_at: datetime


class QuestionDatasetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    dataset_name: str
    dataset_version: str | None
    imported_file_name: str | None
    question_count: int
    created_by_user_id: int
    created_at: datetime
    updated_at: datetime


class QuestionImportErrorRead(BaseModel):
    row_number: int
    message: str


class QuestionImportRead(BaseModel):
    dataset: QuestionDatasetRead
    questions_imported: int
    duplicate_questions: int
    invalid_rows: int
    errors: list[QuestionImportErrorRead]


class EvaluationRunCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    system_version: str | None = Field(default=None, max_length=120)
    notes: str | None = None


class EvaluationRunUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    system_version: str | None = Field(default=None, max_length=120)
    notes: str | None = None


class EvaluationRunRead(EvaluationRunCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    status: Literal["pending", "running", "completed", "failed"]
    last_error: str | None
    processed_question_count: int
    dataset_id: int | None
    batch_document_ids: str | None
    auto_evaluate_enabled: bool
    batch_status: str | None
    current_step: str | None
    completed_steps: str | None
    failed_step: str | None
    batch_error_message: str | None
    batch_started_at: datetime | None
    batch_completed_at: datetime | None
    retrieval_mode: RetrievalMode | None
    generator_model_name: str | None
    embedding_model_name: str | None
    judge_model_name: str | None
    created_by_user_id: int
    created_at: datetime


class RetrievedChunkCreate(BaseModel):
    source_document_id: int
    rank: int = Field(gt=0)
    chunk_text: str = Field(min_length=1)
    section_reference: str | None = Field(default=None, max_length=255)
    relevance_label: RelevanceLabel | None = None
    retrieval_time_ms: int | None = Field(default=None, ge=0)


class RetrievedChunkRead(RetrievedChunkCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    evaluation_run_id: int
    test_question_id: int
    created_at: datetime


class GeneratedAnswerCreate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    answer_text: str = Field(min_length=1)
    model_name: str | None = Field(default=None, max_length=120)
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    generation_time_ms: int | None = Field(default=None, ge=0)
    estimated_cost: Decimal | None = Field(default=None, ge=0)


class GeneratedAnswerRead(GeneratedAnswerCreate):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: int
    evaluation_run_id: int
    test_question_id: int
    created_at: datetime


class RagExecutionRead(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    run_id: int
    status: Literal["completed", "failed"]
    model_name: str
    processed_questions: int
    retrieved_chunks_created: int
    generated_answers_created: int
    retrieval_mode: RetrievalMode
    message: str


class RagExecutionRequest(BaseModel):
    retrieval_mode: RetrievalMode = "keyword"


class BatchExperimentCreate(BaseModel):
    run_name: str = Field(min_length=1, max_length=255)
    dataset_id: int
    document_ids: list[int] = Field(min_length=1)
    retrieval_mode: RetrievalMode = "keyword"
    system_version: str | None = Field(default=None, max_length=120)
    notes: str | None = None
    index_documents: bool = False
    auto_evaluate: bool = True


class EvaluationRecordCreate(BaseModel):
    citation_quality_score: int = Field(ge=1, le=5)
    latency_cost_score: int = Field(ge=1, le=5)
    evidence_faithfulness_score: int = Field(ge=1, le=5)
    answer_relevance_score: int = Field(ge=1, le=5)
    retrieval_quality_score: int = Field(ge=1, le=5)
    reviewer_notes: str | None = None
    suggested_improvement: str | None = None


class EvaluationRecordUpdate(BaseModel):
    citation_quality_score: int | None = Field(default=None, ge=1, le=5)
    latency_cost_score: int | None = Field(default=None, ge=1, le=5)
    evidence_faithfulness_score: int | None = Field(default=None, ge=1, le=5)
    answer_relevance_score: int | None = Field(default=None, ge=1, le=5)
    retrieval_quality_score: int | None = Field(default=None, ge=1, le=5)
    reviewer_notes: str | None = None
    suggested_improvement: str | None = None

    @model_validator(mode="after")
    def validate_scores(self) -> "EvaluationRecordUpdate":
        score_fields = [
            "citation_quality_score",
            "latency_cost_score",
            "evidence_faithfulness_score",
            "answer_relevance_score",
            "retrieval_quality_score",
        ]
        for field_name in score_fields:
            if field_name in self.model_fields_set and getattr(self, field_name) is None:
                raise ValueError(f"{field_name} cannot be null")
        return self


class EvaluationReviewUpdate(BaseModel):
    review_status: ReviewStatus
    citation_quality_score: int | None = Field(default=None, ge=1, le=5)
    latency_cost_score: int | None = Field(default=None, ge=1, le=5)
    evidence_faithfulness_score: int | None = Field(default=None, ge=1, le=5)
    answer_relevance_score: int | None = Field(default=None, ge=1, le=5)
    retrieval_quality_score: int | None = Field(default=None, ge=1, le=5)
    review_notes: str | None = None
    score_change_reason: str | None = None
    reviewer_notes: str | None = None
    suggested_improvement: str | None = None


class EvaluationRecordRead(EvaluationRecordCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    evaluation_run_id: int
    test_question_id: int
    generated_answer_id: int
    reviewer_user_id: int
    overall_score: Decimal
    evaluation_mode: EvaluationMode
    judge_model_name: str | None
    judge_reasoning: str | None
    review_status: ReviewStatus
    reviewed_by_user_id: int | None
    reviewed_at: datetime | None
    review_notes: str | None
    score_change_reason: str | None
    created_at: datetime
    updated_at: datetime


class AutoEvaluationRunRead(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    run_id: int
    evaluated_answers: int
    skipped_answers: int
    judge_model_name: str
    message: str


class DimensionScores(BaseModel):
    citation_quality_score: Decimal | None = None
    latency_cost_score: Decimal | None = None
    evidence_faithfulness_score: Decimal | None = None
    answer_relevance_score: Decimal | None = None
    retrieval_quality_score: Decimal | None = None


class RunQuestionResult(BaseModel):
    question_id: int
    question_text: str
    answer_id: int | None
    answer_text: str | None
    reviewed: bool
    overall_score: Decimal | None
    citation_quality_score: int | None
    latency_cost_score: int | None
    evidence_faithfulness_score: int | None
    answer_relevance_score: int | None
    retrieval_quality_score: int | None
    evaluation_mode: EvaluationMode | None
    judge_model_name: str | None
    review_status: ReviewStatus | None
    reviewed_by_user_id: int | None
    reviewed_at: datetime | None
    expected_source_match: bool | None
    first_relevant_rank: int | None
    retrieved_chunk_count: int
    precision_at_k: Decimal | None
    recall_at_k: Decimal | None
    reciprocal_rank: Decimal | None
    missing_evidence: bool


class RetrievalQuestionMetric(BaseModel):
    question_id: int
    question_text: str
    expected_source: str | None
    expected_source_available: bool
    retrieved_chunk_count: int
    relevant_chunk_count: int
    expected_source_match: bool | None
    first_relevant_rank: int | None
    precision_at_k: Decimal | None
    recall_at_k: Decimal | None
    reciprocal_rank: Decimal | None
    missing_evidence: bool


class RetrievalMetricsRead(BaseModel):
    project_id: int
    run_id: int
    evaluated_question_count: int
    questions_with_expected_source: int
    questions_with_retrieved_chunks: int
    expected_source_hit_count: int
    missing_evidence_count: int
    hit_rate: Decimal | None
    precision_at_k: Decimal | None
    recall_at_k: Decimal | None
    mean_reciprocal_rank: Decimal | None
    chunk_coverage: Decimal | None
    question_metrics: list[RetrievalQuestionMetric]


class RunSummaryRead(BaseModel):
    project_id: int
    run_id: int
    run_name: str
    total_questions: int
    generated_answers: int
    reviewed_answers: int
    review_completion_percent: Decimal
    average_overall_score: Decimal | None
    dimension_averages: DimensionScores
    weakest_dimension: str | None
    retrieval_metrics: RetrievalMetricsRead
    question_results: list[RunQuestionResult]


class ReviewDashboardChunk(BaseModel):
    id: int
    rank: int
    source_document_id: int
    section_reference: str | None
    relevance_label: RelevanceLabel | None
    chunk_text: str


class ReviewDashboardItem(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    question_id: int
    question_text: str
    question_type: QuestionType
    expected_source: str | None
    answer_id: int
    answer_text: str
    model_name: str | None
    evaluation_id: int | None
    evaluation_mode: EvaluationMode | None
    review_status: ReviewStatus
    overall_score: Decimal | None
    citation_quality_score: int | None
    latency_cost_score: int | None
    evidence_faithfulness_score: int | None
    answer_relevance_score: int | None
    retrieval_quality_score: int | None
    judge_model_name: str | None
    judge_reasoning: str | None
    reviewer_notes: str | None
    suggested_improvement: str | None
    review_notes: str | None
    score_change_reason: str | None
    reviewed_by_user_id: int | None
    reviewed_at: datetime | None
    retrieved_chunks: list[ReviewDashboardChunk]


class RunReviewDashboardRead(BaseModel):
    project_id: int
    run_id: int
    run_name: str
    total_answers: int
    pending_review_count: int
    approved_count: int
    needs_revision_count: int
    review_completion_percent: Decimal
    ready_for_release: bool
    approved_average_overall_score: Decimal | None
    items: list[ReviewDashboardItem]


class BatchExperimentRead(BaseModel):
    run: EvaluationRunRead
    rag_execution: RagExecutionRead
    auto_evaluation: AutoEvaluationRunRead | None
    summary: RunSummaryRead
    message: str


class ProjectRunSummaryRead(BaseModel):
    run_id: int
    run_name: str
    generated_answers: int
    reviewed_answers: int
    average_overall_score: Decimal | None


class ProjectSummaryRead(BaseModel):
    project_id: int
    project_name: str
    total_runs: int
    average_overall_score: Decimal | None
    best_run: ProjectRunSummaryRead | None
    weakest_run: ProjectRunSummaryRead | None
    runs: list[ProjectRunSummaryRead]


class RunComparisonRunRead(BaseModel):
    run_id: int
    run_name: str
    system_version: str | None
    retrieval_mode: RetrievalMode | None
    generator_model_name: str | None
    embedding_model_name: str | None
    judge_model_name: str | None
    generated_answers: int
    reviewed_answers: int
    average_overall_score: Decimal | None
    dimension_averages: DimensionScores
    weakest_dimension: str | None


class RunComparisonDeltas(BaseModel):
    overall_score_delta: Decimal | None
    citation_quality_delta: Decimal | None
    latency_cost_delta: Decimal | None
    evidence_faithfulness_delta: Decimal | None
    answer_relevance_delta: Decimal | None
    retrieval_quality_delta: Decimal | None


class RunComparisonQuestionRunResult(BaseModel):
    run_id: int
    answer_id: int | None
    answer_text: str | None
    overall_score: Decimal | None
    reviewed: bool
    evaluation_mode: EvaluationMode | None
    judge_model_name: str | None


class RunComparisonQuestionRead(BaseModel):
    question_id: int
    question_text: str
    best_run_id: int | None
    run_results: list[RunComparisonQuestionRunResult]


class RunComparisonRead(BaseModel):
    project_id: int
    baseline_run_id: int
    compared_run_ids: list[int]
    runs: list[RunComparisonRunRead]
    metric_deltas: dict[str, RunComparisonDeltas]
    question_results: list[RunComparisonQuestionRead]
