import re
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_roles
from app.config import BACKEND_ROOT, get_settings
from app.database import get_db
from app.models import EvaluationRecord, EvaluationRun, Project, SourceDocument, TestQuestion, User
from app.models import GeneratedAnswer, RetrievedChunk
from app.schemas import (
    EvaluationRecordCreate,
    EvaluationRecordRead,
    EvaluationRecordUpdate,
    EvaluationRunCreate,
    EvaluationRunRead,
    EvaluationRunUpdate,
    GeneratedAnswerCreate,
    GeneratedAnswerRead,
    ProjectCreate,
    ProjectRead,
    ProjectUpdate,
    RagExecutionRead,
    RetrievedChunkCreate,
    RetrievedChunkRead,
    SourceDocumentCreate,
    SourceDocumentRead,
    SourceDocumentUpdate,
    TestQuestionCreate,
    TestQuestionRead,
    TestQuestionUpdate,
)
from app.services.rag_execution import RagExecutionError, execute_rag_run


router = APIRouter(prefix="/projects", tags=["projects"])

WritableUser = Annotated[User, Depends(require_roles(["admin", "evaluator"]))]
AuthenticatedUser = Annotated[User, Depends(get_current_user)]
ALLOWED_UPLOAD_EXTENSIONS = {".pdf", ".docx", ".txt", ".csv", ".md"}


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


def calculate_overall_score(record: object) -> Decimal:
    scores = [
        Decimal(getattr(record, "citation_quality_score")),
        Decimal(getattr(record, "latency_cost_score")),
        Decimal(getattr(record, "evidence_faithfulness_score")),
        Decimal(getattr(record, "answer_relevance_score")),
        Decimal(getattr(record, "retrieval_quality_score")),
    ]
    return (sum(scores) / Decimal(len(scores))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


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


@router.patch("/{project_id}", response_model=ProjectRead)
def update_project(
    project_id: int,
    payload: ProjectUpdate,
    db: Annotated[Session, Depends(get_db)],
    _: WritableUser,
) -> Project:
    project = get_project_or_404(db, project_id)
    apply_updates(project, payload)
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
    _: WritableUser,
) -> SourceDocument:
    get_project_or_404(db, project_id)
    document = SourceDocument(**payload.model_dump(), project_id=project_id)
    ensure_valid_document_source(document)
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


@router.post("/{project_id}/documents/upload", response_model=SourceDocumentRead, status_code=status.HTTP_201_CREATED)
def upload_document(
    project_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: WritableUser,
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


@router.get("/{project_id}/runs/{run_id}", response_model=EvaluationRunRead)
def read_run(
    project_id: int,
    run_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: AuthenticatedUser,
) -> EvaluationRun:
    get_project_or_404(db, project_id)
    return get_run_or_404(db, project_id, run_id)


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
    _: WritableUser,
) -> dict[str, object]:
    get_project_or_404(db, project_id)
    run = get_run_or_404(db, project_id, run_id)
    try:
        result = execute_rag_run(db, run, get_settings())
    except RagExecutionError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    return {
        "run_id": result.run_id,
        "status": result.status,
        "model_name": result.model_name,
        "processed_questions": result.processed_questions,
        "retrieved_chunks_created": result.retrieved_chunks_created,
        "generated_answers_created": result.generated_answers_created,
        "message": result.message,
    }


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
    _: WritableUser,
) -> RetrievedChunk:
    validate_output_scope(db, project_id, run_id, question_id, payload.source_document_id)
    chunk = RetrievedChunk(
        **payload.model_dump(),
        evaluation_run_id=run_id,
        test_question_id=question_id,
    )
    db.add(chunk)
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
    _: WritableUser,
) -> GeneratedAnswer:
    validate_output_scope(db, project_id, run_id, question_id)
    answer = GeneratedAnswer(
        **payload.model_dump(),
        evaluation_run_id=run_id,
        test_question_id=question_id,
    )
    db.add(answer)
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
    )
    evaluation.overall_score = calculate_overall_score(evaluation)
    db.add(evaluation)
    db.commit()
    db.refresh(evaluation)
    return evaluation


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
    _: WritableUser,
) -> EvaluationRecord:
    get_project_or_404(db, project_id)
    get_run_or_404(db, project_id, run_id)
    evaluation = get_evaluation_or_404(db, run_id, evaluation_id)
    apply_updates(evaluation, payload)
    evaluation.overall_score = calculate_overall_score(evaluation)
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
