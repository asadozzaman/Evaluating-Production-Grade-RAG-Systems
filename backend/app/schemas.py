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
    created_by_user_id: int
    created_at: datetime
    updated_at: datetime


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
    message: str


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


class EvaluationRecordRead(EvaluationRecordCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    evaluation_run_id: int
    test_question_id: int
    generated_answer_id: int
    reviewer_user_id: int
    overall_score: Decimal
    created_at: datetime
    updated_at: datetime
