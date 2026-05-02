from collections import Counter
import re
import time

from app.services.document_processing import DocumentChunk


STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "does",
    "for",
    "from",
    "how",
    "in",
    "is",
    "of",
    "or",
    "the",
    "to",
    "what",
    "when",
    "where",
    "who",
    "why",
}


def retrieve_top_chunks(question: str, chunks: list[DocumentChunk], limit: int = 3) -> tuple[list[DocumentChunk], int]:
    started = time.perf_counter()
    query_terms = tokenize(question)
    scored: list[tuple[float, int, DocumentChunk]] = []

    for index, chunk in enumerate(chunks):
        chunk_terms = tokenize(chunk.text)
        score = score_chunk(query_terms, chunk_terms)
        if score > 0:
            scored.append((score, index, chunk))

    if not scored:
        scored = [(0.0, index, chunk) for index, chunk in enumerate(chunks[:limit])]

    ranked = [chunk for _, _, chunk in sorted(scored, key=lambda item: (-item[0], item[1]))[:limit]]
    elapsed_ms = max(0, round((time.perf_counter() - started) * 1000))
    return ranked, elapsed_ms


def score_chunk(query_terms: list[str], chunk_terms: list[str]) -> float:
    if not query_terms or not chunk_terms:
        return 0.0

    chunk_counts = Counter(chunk_terms)
    overlap = sum(chunk_counts.get(term, 0) for term in query_terms)
    unique_overlap = len(set(query_terms).intersection(chunk_counts))
    return overlap + unique_overlap * 2


def tokenize(value: str) -> list[str]:
    return [token for token in re.findall(r"[a-zA-Z0-9]+", value.lower()) if token not in STOP_WORDS and len(token) > 1]
