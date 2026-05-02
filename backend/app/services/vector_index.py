import json
import math
import time
from dataclasses import dataclass

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import DocumentChunk as StoredDocumentChunk
from app.models import SourceDocument
from app.services.document_processing import DocumentChunk as RuntimeDocumentChunk
from app.services.document_processing import chunk_document, extract_document_text
from app.services.gemini import GeminiClient, normalize_model_name


@dataclass(frozen=True)
class DocumentIndexResult:
    document_id: int
    chunks_indexed: int
    embedding_model: str
    message: str


def index_source_document(
    db: Session,
    document: SourceDocument,
    settings: Settings,
    gemini_client: GeminiClient | None = None,
) -> DocumentIndexResult:
    text = extract_document_text(document)
    chunks = chunk_document(document, text)
    if not chunks:
        raise ValueError("No extractable document text found. Upload a .txt, .md, .csv, .docx, or .pdf file with readable text.")

    client = gemini_client or GeminiClient(settings)
    embedding_model = normalize_model_name(settings.default_embedding_model)

    db.execute(delete(StoredDocumentChunk).where(StoredDocumentChunk.source_document_id == document.id))
    for index, chunk in enumerate(chunks, start=1):
        embedding = client.embed_text(chunk.text)
        db.add(
            StoredDocumentChunk(
                source_document_id=document.id,
                chunk_index=index,
                chunk_text=chunk.text,
                section_reference=chunk.section_reference,
                embedding_model=embedding_model,
                embedding_json=json.dumps(embedding),
            )
        )
    db.commit()

    return DocumentIndexResult(
        document_id=document.id,
        chunks_indexed=len(chunks),
        embedding_model=embedding_model,
        message="Document indexed for vector retrieval.",
    )


def retrieve_vector_chunks(
    question_embedding: list[float],
    stored_chunks: list[StoredDocumentChunk],
    limit: int = 3,
) -> tuple[list[RuntimeDocumentChunk], int]:
    started = time.perf_counter()
    scored: list[tuple[float, int, StoredDocumentChunk]] = []
    for index, stored_chunk in enumerate(stored_chunks):
        embedding = parse_embedding(stored_chunk.embedding_json)
        score = cosine_similarity(question_embedding, embedding)
        scored.append((score, index, stored_chunk))

    ranked = [
        RuntimeDocumentChunk(
            source_document_id=stored_chunk.source_document_id,
            source_title=stored_chunk.source_document.title,
            text=stored_chunk.chunk_text,
            section_reference=stored_chunk.section_reference or f"{stored_chunk.source_document.title} - chunk {stored_chunk.chunk_index}",
        )
        for _, _, stored_chunk in sorted(scored, key=lambda item: (-item[0], item[1]))[:limit]
    ]
    elapsed_ms = max(0, round((time.perf_counter() - started) * 1000))
    return ranked, elapsed_ms


def list_indexed_chunks(db: Session, project_id: int, document_ids: list[int] | None = None) -> list[StoredDocumentChunk]:
    statement = select(StoredDocumentChunk).join(SourceDocument).where(SourceDocument.project_id == project_id)
    if document_ids:
        statement = statement.where(SourceDocument.id.in_(document_ids))
    return list(
        db.scalars(
            statement.order_by(SourceDocument.created_at.asc(), SourceDocument.id.asc(), StoredDocumentChunk.chunk_index.asc())
        ).all()
    )


def parse_embedding(value: str) -> list[float]:
    parsed = json.loads(value)
    return [float(item) for item in parsed]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    dot_product = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot_product / (left_norm * right_norm)
