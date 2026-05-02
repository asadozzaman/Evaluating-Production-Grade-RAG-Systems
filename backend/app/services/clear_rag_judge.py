import json
import re
from dataclasses import dataclass

from app.models import GeneratedAnswer, RetrievedChunk, TestQuestion
from app.services.gemini import GeminiClient


@dataclass(frozen=True)
class ClearRagJudgment:
    citation_quality_score: int
    latency_cost_score: int
    evidence_faithfulness_score: int
    answer_relevance_score: int
    retrieval_quality_score: int
    reviewer_notes: str
    suggested_improvement: str
    judge_reasoning: str
    judge_model_name: str


def judge_clear_rag_answer(
    question: TestQuestion,
    answer: GeneratedAnswer,
    chunks: list[RetrievedChunk],
    client: GeminiClient,
) -> ClearRagJudgment:
    prompt = build_judge_prompt(question, answer, chunks)
    response = client.generate_answer(prompt)
    data = parse_json_object(response.text)
    return ClearRagJudgment(
        citation_quality_score=score_value(data, "citation_quality_score"),
        latency_cost_score=score_value(data, "latency_cost_score"),
        evidence_faithfulness_score=score_value(data, "evidence_faithfulness_score"),
        answer_relevance_score=score_value(data, "answer_relevance_score"),
        retrieval_quality_score=score_value(data, "retrieval_quality_score"),
        reviewer_notes=str(data.get("reviewer_notes") or "").strip()[:3000],
        suggested_improvement=str(data.get("suggested_improvement") or "").strip()[:3000],
        judge_reasoning=str(data.get("judge_reasoning") or "").strip()[:5000],
        judge_model_name=response.model_name,
    )


def build_judge_prompt(question: TestQuestion, answer: GeneratedAnswer, chunks: list[RetrievedChunk]) -> str:
    evidence = "\n\n".join(
        (
            f"[{chunk.rank}] Source document id: {chunk.source_document_id}\n"
            f"Section: {chunk.section_reference or 'Not provided'}\n"
            f"Relevance label: {chunk.relevance_label or 'Not labeled'}\n"
            f"Retrieval time ms: {chunk.retrieval_time_ms if chunk.retrieval_time_ms is not None else 'Not provided'}\n"
            f"Text: {chunk.chunk_text}"
        )
        for chunk in chunks
    )
    if not evidence:
        evidence = "No retrieved chunks were recorded for this answer."

    return (
        "You are an automated CLEAR-RAG evaluator. Score the generated answer using only the question, expected source, "
        "retrieved evidence, answer text, and timing/cost metadata below.\n\n"
        "Rubric dimensions, each scored from 1 to 5:\n"
        "1. citation_quality_score: citations are present, specific, and point to the provided evidence.\n"
        "2. latency_cost_score: response is efficient given generation time, tokens, and cost.\n"
        "3. evidence_faithfulness_score: answer claims are fully supported by retrieved evidence.\n"
        "4. answer_relevance_score: answer directly addresses the test question.\n"
        "5. retrieval_quality_score: retrieved chunks are relevant, sufficient, and well ranked.\n\n"
        "Return JSON only. No markdown. No prose outside JSON. Use this exact shape:\n"
        "{\n"
        '  "citation_quality_score": 1,\n'
        '  "latency_cost_score": 1,\n'
        '  "evidence_faithfulness_score": 1,\n'
        '  "answer_relevance_score": 1,\n'
        '  "retrieval_quality_score": 1,\n'
        '  "reviewer_notes": "short summary of the score",\n'
        '  "suggested_improvement": "one practical improvement",\n'
        '  "judge_reasoning": "brief evidence-based reasoning"\n'
        "}\n\n"
        f"Question:\n{question.question_text}\n\n"
        f"Question type: {question.question_type}\n"
        f"Expected source: {question.expected_source or 'Not provided'}\n\n"
        f"Generated answer:\n{answer.answer_text}\n\n"
        "Generation metadata:\n"
        f"Model: {answer.model_name or 'Not provided'}\n"
        f"Input tokens: {answer.input_tokens if answer.input_tokens is not None else 'Not provided'}\n"
        f"Output tokens: {answer.output_tokens if answer.output_tokens is not None else 'Not provided'}\n"
        f"Generation time ms: {answer.generation_time_ms if answer.generation_time_ms is not None else 'Not provided'}\n"
        f"Estimated cost: {answer.estimated_cost if answer.estimated_cost is not None else 'Not provided'}\n\n"
        f"Retrieved evidence:\n{evidence}\n"
    )


def parse_json_object(value: str) -> dict:
    cleaned = value.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if not match:
            raise ValueError("Judge response did not contain a JSON object.")
        parsed = json.loads(match.group(0))
    if not isinstance(parsed, dict):
        raise ValueError("Judge response JSON must be an object.")
    return parsed


def score_value(data: dict, key: str) -> int:
    value = int(data[key])
    if value < 1 or value > 5:
        raise ValueError(f"{key} must be between 1 and 5.")
    return value
