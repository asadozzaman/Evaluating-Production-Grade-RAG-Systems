from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import EvaluationRun, GeneratedAnswer, RetrievedChunk, SourceDocument, TestQuestion
from app.services.document_processing import DocumentChunk, chunk_document, extract_document_text
from app.services.gemini import GeminiAnswer, GeminiClient, normalize_model_name
from app.services.retrieval import retrieve_top_chunks
from app.services.vector_index import list_indexed_chunks, retrieve_vector_chunks


@dataclass(frozen=True)
class RagExecutionResult:
    run_id: int
    status: str
    model_name: str
    processed_questions: int
    retrieved_chunks_created: int
    generated_answers_created: int
    retrieval_mode: str
    message: str


class RagExecutionError(Exception):
    def __init__(self, message: str, status_code: int = 422) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def execute_rag_run(
    db: Session,
    run: EvaluationRun,
    settings: Settings,
    gemini_client: GeminiClient | None = None,
    retrieval_mode: str = "keyword",
) -> RagExecutionResult:
    questions = list(
        db.scalars(
            select(TestQuestion)
            .where(TestQuestion.project_id == run.project_id)
            .order_by(TestQuestion.created_at.asc(), TestQuestion.id.asc())
        ).all()
    )
    documents = list(
        db.scalars(
            select(SourceDocument)
            .where(SourceDocument.project_id == run.project_id)
            .order_by(SourceDocument.created_at.asc(), SourceDocument.id.asc())
        ).all()
    )

    if not questions:
        raise RagExecutionError("Create at least one test question before running Gemini RAG.")
    if not documents:
        raise RagExecutionError("Upload at least one source document before running Gemini RAG.")

    if retrieval_mode not in {"keyword", "vector"}:
        raise RagExecutionError("retrieval_mode must be keyword or vector.")

    all_chunks = build_chunks(documents) if retrieval_mode == "keyword" else []
    indexed_chunks = list_indexed_chunks(db, run.project_id) if retrieval_mode == "vector" else []
    if retrieval_mode == "keyword" and not all_chunks:
        raise RagExecutionError("No extractable document text found. Upload a .txt, .md, .csv, .docx, or .pdf file with readable text.")
    if retrieval_mode == "vector" and not indexed_chunks:
        raise RagExecutionError("Index at least one source document before running vector retrieval.")

    client = gemini_client or GeminiClient(settings)
    run.status = "running"
    run.last_error = None
    run.processed_question_count = 0
    run.retrieval_mode = retrieval_mode
    run.generator_model_name = normalize_model_name(settings.default_llm_model)
    run.embedding_model_name = normalize_model_name(settings.default_embedding_model) if retrieval_mode == "vector" else None
    db.commit()

    clear_previous_outputs(db, run.id)
    retrieved_count = 0
    answer_count = 0

    try:
        for question in questions:
            if retrieval_mode == "vector":
                question_embedding = client.embed_text(question.question_text)
                selected_chunks, retrieval_time_ms = retrieve_vector_chunks(question_embedding, indexed_chunks)
            else:
                selected_chunks, retrieval_time_ms = retrieve_top_chunks(question.question_text, all_chunks)
            saved_chunks = save_retrieved_chunks(db, run.id, question.id, selected_chunks, retrieval_time_ms)
            retrieved_count += len(saved_chunks)

            prompt = build_prompt(question.question_text, selected_chunks)
            answer = client.generate_answer(prompt)
            save_generated_answer(db, run.id, question.id, answer)
            answer_count += 1
            run.processed_question_count += 1
            db.commit()
    except Exception as exc:
        db.rollback()
        run.status = "failed"
        run.last_error = str(exc)
        db.commit()
        raise RagExecutionError(str(exc), status_code=502) from exc

    run.status = "completed"
    run.last_error = None
    db.commit()

    model_name = run.generator_model_name or normalize_model_name(settings.default_llm_model)
    return RagExecutionResult(
        run_id=run.id,
        status=run.status,
        model_name=model_name,
        processed_questions=run.processed_question_count,
        retrieved_chunks_created=retrieved_count,
        generated_answers_created=answer_count,
        retrieval_mode=retrieval_mode,
        message=f"Gemini RAG execution completed with {retrieval_mode} retrieval.",
    )


def build_chunks(documents: list[SourceDocument]) -> list[DocumentChunk]:
    chunks: list[DocumentChunk] = []
    for document in documents:
        text = extract_document_text(document)
        chunks.extend(chunk_document(document, text))
    return chunks


def clear_previous_outputs(db: Session, run_id: int) -> None:
    db.execute(delete(RetrievedChunk).where(RetrievedChunk.evaluation_run_id == run_id))
    db.execute(delete(GeneratedAnswer).where(GeneratedAnswer.evaluation_run_id == run_id))
    db.commit()


def save_retrieved_chunks(
    db: Session,
    run_id: int,
    question_id: int,
    chunks: list[DocumentChunk],
    retrieval_time_ms: int,
) -> list[RetrievedChunk]:
    saved: list[RetrievedChunk] = []
    for index, chunk in enumerate(chunks, start=1):
        saved_chunk = RetrievedChunk(
            evaluation_run_id=run_id,
            test_question_id=question_id,
            source_document_id=chunk.source_document_id,
            rank=index,
            chunk_text=chunk.text,
            section_reference=chunk.section_reference,
            relevance_label=relevance_label_for_rank(index),
            retrieval_time_ms=retrieval_time_ms,
        )
        db.add(saved_chunk)
        saved.append(saved_chunk)
    db.flush()
    return saved


def save_generated_answer(db: Session, run_id: int, question_id: int, answer: GeminiAnswer) -> GeneratedAnswer:
    generated_answer = GeneratedAnswer(
        evaluation_run_id=run_id,
        test_question_id=question_id,
        answer_text=answer.text,
        model_name=answer.model_name,
        input_tokens=answer.input_tokens,
        output_tokens=answer.output_tokens,
        generation_time_ms=answer.generation_time_ms,
        estimated_cost=Decimal("0"),
    )
    db.add(generated_answer)
    db.flush()
    return generated_answer


def build_prompt(question: str, chunks: list[DocumentChunk]) -> str:
    evidence = "\n\n".join(
        f"[{index}] Source: {chunk.source_title}\nSection: {chunk.section_reference}\nText: {chunk.text}"
        for index, chunk in enumerate(chunks, start=1)
    )
    return (
        "You are answering a production RAG evaluation question.\n"
        "Use only the evidence below. If the evidence is insufficient, say that the evidence is insufficient.\n"
        "Answer concisely and cite evidence numbers like [1].\n\n"
        f"Question:\n{question}\n\n"
        f"Evidence:\n{evidence}\n\n"
        "Answer:"
    )


def relevance_label_for_rank(rank: int) -> str:
    if rank == 1:
        return "high"
    if rank == 2:
        return "medium"
    return "low"
