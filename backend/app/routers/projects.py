import re
import csv
import io
import json
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Response, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_roles
from app.config import BACKEND_ROOT, get_settings
from app.database import get_db
from app.models import DocumentChunk, EvaluationRecord, EvaluationRun, Project, QuestionDataset, SourceDocument, TestQuestion, User
from app.models import GeneratedAnswer, RetrievedChunk
from app.schemas import (
    AutoEvaluationRunRead,
    BatchExperimentCreate,
    BatchExperimentRead,
    DocumentChunkRead,
    DocumentIndexRead,
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
    ProjectSummaryRead,
    QuestionDatasetRead,
    QuestionImportRead,
    RagExecutionRequest,
    RagExecutionRead,
    RunComparisonRead,
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


def decimal_average(values: list[Decimal]) -> Decimal | None:
    if not values:
        return None
    return (sum(values) / Decimal(len(values))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def percent(part: int, whole: int) -> Decimal:
    if whole == 0:
        return Decimal("0.00")
    return (Decimal(part) * Decimal("100") / Decimal(whole)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


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
    _: WritableUser,
    payload: RagExecutionRequest | None = None,
) -> dict[str, object]:
    get_project_or_404(db, project_id)
    run = get_run_or_404(db, project_id, run_id)
    retrieval_mode = payload.retrieval_mode if payload else "keyword"
    try:
        result = execute_rag_run(db, run, get_settings(), retrieval_mode=retrieval_mode)
    except RagExecutionError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
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
            )
            evaluation.overall_score = calculate_overall_score(evaluation)
            db.add(evaluation)
            evaluated_answers += 1
        run.judge_model_name = judge_model_name
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

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
