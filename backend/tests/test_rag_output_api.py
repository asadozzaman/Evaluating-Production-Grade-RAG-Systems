from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import EvaluationRun, Role, User
from app.security import hash_password
from app.services.gemini import GeminiAnswer


@pytest.fixture()
def client_and_db(tmp_path: Path) -> Generator[tuple[TestClient, sessionmaker[Session]]]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    from app.config import get_settings

    settings = get_settings()
    original_upload_dir = settings.upload_dir
    settings.upload_dir = str(tmp_path / "uploads")

    def override_get_db() -> Generator[Session]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestingSessionLocal() as db:
            db.add_all(
                [
                    Role(name="admin", description="Admin role"),
                    Role(name="evaluator", description="Evaluator role"),
                    Role(name="viewer", description="Viewer role"),
                ]
            )
            db.commit()
        yield TestClient(app), TestingSessionLocal
    finally:
        settings.upload_dir = original_upload_dir
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)


def create_user(db_factory: sessionmaker[Session], email: str, role_name: str) -> None:
    with db_factory() as db:
        role = db.scalar(select(Role).where(Role.name == role_name))
        assert role is not None
        user = User(
            email=email,
            full_name=email.split("@")[0],
            hashed_password=hash_password("StrongPass123!"),
            roles=[role],
        )
        db.add(user)
        db.commit()


def login(client: TestClient, email: str) -> str:
    response = client.post("/auth/login", json={"email": email, "password": "StrongPass123!"})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def create_setup_graph(client: TestClient, token: str, name: str = "Output Intake Project") -> dict[str, int]:
    project = client.post(
        "/projects",
        json={
            "name": name,
            "system_type": "internal_knowledge_assistant",
            "target_users": "Employees",
        },
        headers=auth_headers(token),
    )
    assert project.status_code == 201, project.text
    project_id = project.json()["id"]

    document = client.post(
        f"/projects/{project_id}/documents",
        json={
            "title": "HR Leave Policy",
            "document_type": "policy",
            "source_kind": "uri",
            "source_uri": "memory://hr-leave-policy",
            "version": "v1",
        },
        headers=auth_headers(token),
    )
    assert document.status_code == 201, document.text

    question = client.post(
        f"/projects/{project_id}/questions",
        json={
            "question_text": "How many annual leave days does an employee receive after one year?",
            "question_type": "simple_factual",
            "expected_source": "HR Leave Policy, Section 1.1",
        },
        headers=auth_headers(token),
    )
    assert question.status_code == 201, question.text

    run = client.post(
        f"/projects/{project_id}/runs",
        json={"name": "Baseline Evaluation", "system_version": "v1"},
        headers=auth_headers(token),
    )
    assert run.status_code == 201, run.text

    return {
        "project_id": project_id,
        "document_id": document.json()["id"],
        "question_id": question.json()["id"],
        "run_id": run.json()["id"],
    }


def test_rag_output_intake_and_role_access(client_and_db: tuple[TestClient, sessionmaker[Session]]) -> None:
    client, db_factory = client_and_db
    create_user(db_factory, "admin@example.com", "admin")
    create_user(db_factory, "viewer@example.com", "viewer")

    admin_token = login(client, "admin@example.com")
    viewer_token = login(client, "viewer@example.com")
    graph = create_setup_graph(client, admin_token)

    chunk_path = (
        f"/projects/{graph['project_id']}/runs/{graph['run_id']}"
        f"/questions/{graph['question_id']}/retrieved-chunks"
    )
    answer_path = (
        f"/projects/{graph['project_id']}/runs/{graph['run_id']}"
        f"/questions/{graph['question_id']}/generated-answers"
    )

    viewer_chunk = client.post(
        chunk_path,
        json={
            "source_document_id": graph["document_id"],
            "rank": 1,
            "chunk_text": "Viewer should not create chunks.",
        },
        headers=auth_headers(viewer_token),
    )
    assert viewer_chunk.status_code == 403

    chunk = client.post(
        chunk_path,
        json={
            "source_document_id": graph["document_id"],
            "rank": 1,
            "chunk_text": "Full-time employees receive 20 days of annual leave after one year.",
            "section_reference": "Section 1.1",
            "relevance_label": "high",
            "retrieval_time_ms": 120,
        },
        headers=auth_headers(admin_token),
    )
    assert chunk.status_code == 201, chunk.text
    assert chunk.json()["rank"] == 1

    invalid_chunk = client.post(
        chunk_path,
        json={
            "source_document_id": graph["document_id"],
            "rank": 0,
            "chunk_text": "Rank must be positive.",
        },
        headers=auth_headers(admin_token),
    )
    assert invalid_chunk.status_code == 422

    answer = client.post(
        answer_path,
        json={
            "answer_text": "After one year, a full-time employee receives 20 days of annual leave.",
            "model_name": "test-model",
            "input_tokens": 1200,
            "output_tokens": 95,
            "generation_time_ms": 1800,
            "estimated_cost": "0.0125",
        },
        headers=auth_headers(admin_token),
    )
    assert answer.status_code == 201, answer.text
    assert answer.json()["model_name"] == "test-model"

    invalid_answer = client.post(
        answer_path,
        json={
            "answer_text": "Negative tokens should fail.",
            "input_tokens": -1,
        },
        headers=auth_headers(admin_token),
    )
    assert invalid_answer.status_code == 422

    listed_chunks = client.get(chunk_path, headers=auth_headers(viewer_token))
    assert listed_chunks.status_code == 200
    assert len(listed_chunks.json()) == 1

    listed_answers = client.get(answer_path, headers=auth_headers(viewer_token))
    assert listed_answers.status_code == 200
    assert len(listed_answers.json()) == 1

    delete_chunk = client.delete(
        f"{chunk_path}/{chunk.json()['id']}",
        headers=auth_headers(admin_token),
    )
    assert delete_chunk.status_code == 204

    delete_answer = client.delete(
        f"{answer_path}/{answer.json()['id']}",
        headers=auth_headers(admin_token),
    )
    assert delete_answer.status_code == 204


def test_rag_output_scope_validation(client_and_db: tuple[TestClient, sessionmaker[Session]]) -> None:
    client, db_factory = client_and_db
    create_user(db_factory, "admin@example.com", "admin")
    admin_token = login(client, "admin@example.com")
    graph_one = create_setup_graph(client, admin_token, "Project One")
    graph_two = create_setup_graph(client, admin_token, "Project Two")

    wrong_run_path = (
        f"/projects/{graph_one['project_id']}/runs/{graph_two['run_id']}"
        f"/questions/{graph_one['question_id']}/generated-answers"
    )
    wrong_run = client.post(
        wrong_run_path,
        json={"answer_text": "Run belongs to another project."},
        headers=auth_headers(admin_token),
    )
    assert wrong_run.status_code == 404

    wrong_question_path = (
        f"/projects/{graph_one['project_id']}/runs/{graph_one['run_id']}"
        f"/questions/{graph_two['question_id']}/generated-answers"
    )
    wrong_question = client.post(
        wrong_question_path,
        json={"answer_text": "Question belongs to another project."},
        headers=auth_headers(admin_token),
    )
    assert wrong_question.status_code == 404

    wrong_document_path = (
        f"/projects/{graph_one['project_id']}/runs/{graph_one['run_id']}"
        f"/questions/{graph_one['question_id']}/retrieved-chunks"
    )
    wrong_document = client.post(
        wrong_document_path,
        json={
            "source_document_id": graph_two["document_id"],
            "rank": 1,
            "chunk_text": "Document belongs to another project.",
        },
        headers=auth_headers(admin_token),
    )
    assert wrong_document.status_code == 404


def test_execute_rag_run_with_uploaded_text_and_mocked_gemini(
    client_and_db: tuple[TestClient, sessionmaker[Session]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeGeminiClient:
        def __init__(self, settings: object) -> None:
            self.settings = settings

        def generate_answer(self, prompt: str) -> GeminiAnswer:
            assert "Employees receive 18 annual leave days" in prompt
            return GeminiAnswer(
                text="Employees receive 18 annual leave days after one year of service. [1]",
                model_name="gemini-test",
                input_tokens=80,
                output_tokens=14,
                generation_time_ms=25,
            )

    monkeypatch.setattr("app.services.rag_execution.GeminiClient", FakeGeminiClient)

    client, db_factory = client_and_db
    create_user(db_factory, "admin@example.com", "admin")
    create_user(db_factory, "viewer@example.com", "viewer")
    admin_token = login(client, "admin@example.com")
    viewer_token = login(client, "viewer@example.com")

    project = create_setup_graph(client, admin_token, "Automatic Gemini RAG")
    uploaded_document = client.post(
        f"/projects/{project['project_id']}/documents/upload",
        data={"title": "Uploaded HR Policy", "document_type": "policy", "version": "v1"},
        files={
            "file": (
                "hr-policy.txt",
                b"Employees receive 18 annual leave days after completing one year of service.",
                "text/plain",
            )
        },
        headers=auth_headers(admin_token),
    )
    assert uploaded_document.status_code == 201, uploaded_document.text

    viewer_execute = client.post(
        f"/projects/{project['project_id']}/runs/{project['run_id']}/execute",
        headers=auth_headers(viewer_token),
    )
    assert viewer_execute.status_code == 403

    executed = client.post(
        f"/projects/{project['project_id']}/runs/{project['run_id']}/execute",
        headers=auth_headers(admin_token),
    )
    assert executed.status_code == 200, executed.text
    payload = executed.json()
    assert payload["status"] == "completed"
    assert payload["processed_questions"] == 1
    assert payload["retrieved_chunks_created"] >= 1
    assert payload["generated_answers_created"] == 1
    assert payload["retrieval_mode"] == "keyword"

    run = client.get(
        f"/projects/{project['project_id']}/runs/{project['run_id']}",
        headers=auth_headers(admin_token),
    )
    assert run.status_code == 200
    assert run.json()["status"] == "completed"

    chunks = client.get(
        f"/projects/{project['project_id']}/runs/{project['run_id']}/questions/{project['question_id']}/retrieved-chunks",
        headers=auth_headers(admin_token),
    )
    assert chunks.status_code == 200
    assert "18 annual leave days" in chunks.json()[0]["chunk_text"]

    answers = client.get(
        f"/projects/{project['project_id']}/runs/{project['run_id']}/questions/{project['question_id']}/generated-answers",
        headers=auth_headers(admin_token),
    )
    assert answers.status_code == 200
    assert answers.json()[0]["model_name"] == "gemini-test"


def test_document_indexing_and_vector_rag_with_mocked_gemini(
    client_and_db: tuple[TestClient, sessionmaker[Session]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeGeminiClient:
        def __init__(self, settings: object) -> None:
            self.settings = settings

        def embed_text(self, text: str) -> list[float]:
            lowered = text.lower()
            if "annual leave" in lowered or "leave days" in lowered:
                return [1.0, 0.0, 0.0]
            return [0.0, 1.0, 0.0]

        def generate_answer(self, prompt: str) -> GeminiAnswer:
            assert "Employees receive 22 annual leave days" in prompt
            return GeminiAnswer(
                text="Employees receive 22 annual leave days after one year of service. [1]",
                model_name="gemini-test",
                input_tokens=90,
                output_tokens=15,
                generation_time_ms=30,
            )

    monkeypatch.setattr("app.services.vector_index.GeminiClient", FakeGeminiClient)
    monkeypatch.setattr("app.services.rag_execution.GeminiClient", FakeGeminiClient)

    client, db_factory = client_and_db
    create_user(db_factory, "admin@example.com", "admin")
    create_user(db_factory, "viewer@example.com", "viewer")
    admin_token = login(client, "admin@example.com")
    viewer_token = login(client, "viewer@example.com")
    project = create_setup_graph(client, admin_token, "Vector Gemini RAG")

    uploaded_document = client.post(
        f"/projects/{project['project_id']}/documents/upload",
        data={"title": "Vector HR Policy", "document_type": "policy", "version": "v1"},
        files={
            "file": (
                "vector-hr-policy.txt",
                b"Employees receive 22 annual leave days after completing one year of service.",
                "text/plain",
            )
        },
        headers=auth_headers(admin_token),
    )
    assert uploaded_document.status_code == 201, uploaded_document.text
    document_id = uploaded_document.json()["id"]

    viewer_index = client.post(
        f"/projects/{project['project_id']}/documents/{document_id}/index",
        headers=auth_headers(viewer_token),
    )
    assert viewer_index.status_code == 403

    indexed = client.post(
        f"/projects/{project['project_id']}/documents/{document_id}/index",
        headers=auth_headers(admin_token),
    )
    assert indexed.status_code == 200, indexed.text
    assert indexed.json()["chunks_indexed"] == 1
    assert indexed.json()["embedding_model"] == "gemini-embedding-001"

    chunks = client.get(
        f"/projects/{project['project_id']}/documents/{document_id}/chunks",
        headers=auth_headers(viewer_token),
    )
    assert chunks.status_code == 200, chunks.text
    assert len(chunks.json()) == 1
    assert chunks.json()[0]["embedding_model"] == "gemini-embedding-001"

    executed = client.post(
        f"/projects/{project['project_id']}/runs/{project['run_id']}/execute",
        json={"retrieval_mode": "vector"},
        headers=auth_headers(admin_token),
    )
    assert executed.status_code == 200, executed.text
    payload = executed.json()
    assert payload["status"] == "completed"
    assert payload["retrieval_mode"] == "vector"
    assert payload["retrieved_chunks_created"] == 1
    assert payload["generated_answers_created"] == 1


def test_clear_rag_evaluation_scoring_and_role_access(
    client_and_db: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, db_factory = client_and_db
    create_user(db_factory, "admin@example.com", "admin")
    create_user(db_factory, "viewer@example.com", "viewer")
    admin_token = login(client, "admin@example.com")
    viewer_token = login(client, "viewer@example.com")
    graph = create_setup_graph(client, admin_token, "CLEAR-RAG Scoring")

    answer_path = (
        f"/projects/{graph['project_id']}/runs/{graph['run_id']}"
        f"/questions/{graph['question_id']}/generated-answers"
    )
    answer = client.post(
        answer_path,
        json={
            "answer_text": "Employees receive 20 days of annual leave after one year.",
            "model_name": "gemini-test",
            "input_tokens": 100,
            "output_tokens": 20,
            "generation_time_ms": 900,
            "estimated_cost": "0.000000",
        },
        headers=auth_headers(admin_token),
    )
    assert answer.status_code == 201, answer.text
    answer_id = answer.json()["id"]

    evaluation_path = (
        f"/projects/{graph['project_id']}/runs/{graph['run_id']}"
        f"/questions/{graph['question_id']}/answers/{answer_id}/evaluations"
    )

    viewer_score = client.post(
        evaluation_path,
        json={
            "citation_quality_score": 5,
            "latency_cost_score": 4,
            "evidence_faithfulness_score": 5,
            "answer_relevance_score": 5,
            "retrieval_quality_score": 4,
        },
        headers=auth_headers(viewer_token),
    )
    assert viewer_score.status_code == 403

    evaluation = client.post(
        evaluation_path,
        json={
            "citation_quality_score": 5,
            "latency_cost_score": 4,
            "evidence_faithfulness_score": 5,
            "answer_relevance_score": 5,
            "retrieval_quality_score": 4,
            "reviewer_notes": "Accurate and grounded in evidence.",
            "suggested_improvement": "Reduce extra retrieved chunks.",
        },
        headers=auth_headers(admin_token),
    )
    assert evaluation.status_code == 201, evaluation.text
    evaluation_payload = evaluation.json()
    assert evaluation_payload["overall_score"] == "4.60"
    assert evaluation_payload["evaluation_mode"] == "human"
    assert evaluation_payload["reviewer_notes"] == "Accurate and grounded in evidence."

    invalid_score = client.post(
        evaluation_path,
        json={
            "citation_quality_score": 6,
            "latency_cost_score": 4,
            "evidence_faithfulness_score": 5,
            "answer_relevance_score": 5,
            "retrieval_quality_score": 4,
        },
        headers=auth_headers(admin_token),
    )
    assert invalid_score.status_code == 422

    list_evaluations = client.get(
        f"/projects/{graph['project_id']}/runs/{graph['run_id']}/evaluations",
        headers=auth_headers(viewer_token),
    )
    assert list_evaluations.status_code == 200
    assert len(list_evaluations.json()) == 1

    update_evaluation = client.patch(
        f"/projects/{graph['project_id']}/runs/{graph['run_id']}/evaluations/{evaluation_payload['id']}",
        json={
            "latency_cost_score": 5,
            "retrieval_quality_score": 5,
            "reviewer_notes": "Strong answer across all dimensions.",
        },
        headers=auth_headers(admin_token),
    )
    assert update_evaluation.status_code == 200, update_evaluation.text
    assert update_evaluation.json()["overall_score"] == "5.00"

    run_summary = client.get(
        f"/projects/{graph['project_id']}/runs/{graph['run_id']}/summary",
        headers=auth_headers(viewer_token),
    )
    assert run_summary.status_code == 200, run_summary.text
    run_summary_payload = run_summary.json()
    assert run_summary_payload["total_questions"] == 1
    assert run_summary_payload["generated_answers"] == 1
    assert run_summary_payload["reviewed_answers"] == 1
    assert run_summary_payload["review_completion_percent"] == "100.00"
    assert run_summary_payload["average_overall_score"] == "5.00"
    assert run_summary_payload["weakest_dimension"] == "Citation Quality"
    assert run_summary_payload["question_results"][0]["reviewed"] is True

    project_summary = client.get(
        f"/projects/{graph['project_id']}/summary",
        headers=auth_headers(viewer_token),
    )
    assert project_summary.status_code == 200, project_summary.text
    assert project_summary.json()["average_overall_score"] == "5.00"

    json_export = client.get(
        f"/projects/{graph['project_id']}/runs/{graph['run_id']}/export.json",
        headers=auth_headers(viewer_token),
    )
    assert json_export.status_code == 200
    assert json_export.json()["question_results"][0]["answer_id"] == answer_id

    csv_export = client.get(
        f"/projects/{graph['project_id']}/runs/{graph['run_id']}/export.csv",
        headers=auth_headers(viewer_token),
    )
    assert csv_export.status_code == 200
    assert "question_id,question_text,answer_id" in csv_export.text
    assert "Employees receive 20 days" in csv_export.text

    viewer_delete = client.delete(
        f"/projects/{graph['project_id']}/runs/{graph['run_id']}/evaluations/{evaluation_payload['id']}",
        headers=auth_headers(viewer_token),
    )
    assert viewer_delete.status_code == 403

    delete_evaluation = client.delete(
        f"/projects/{graph['project_id']}/runs/{graph['run_id']}/evaluations/{evaluation_payload['id']}",
        headers=auth_headers(admin_token),
    )
    assert delete_evaluation.status_code == 204


def test_automated_clear_rag_evaluation_and_role_access(
    client_and_db: tuple[TestClient, sessionmaker[Session]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeGeminiJudgeClient:
        def __init__(self, settings: object) -> None:
            self.settings = settings

        def generate_answer(self, prompt: str) -> GeminiAnswer:
            assert "Full-time employees receive 20 days" in prompt
            return GeminiAnswer(
                text=(
                    "{"
                    '"citation_quality_score": 5,'
                    '"latency_cost_score": 4,'
                    '"evidence_faithfulness_score": 5,'
                    '"answer_relevance_score": 5,'
                    '"retrieval_quality_score": 4,'
                    '"reviewer_notes": "Answer is grounded in retrieved policy evidence.",'
                    '"suggested_improvement": "Keep the citation tied to the exact policy section.",'
                    '"judge_reasoning": "The answer directly uses the retrieved annual leave evidence."'
                    "}"
                ),
                model_name="gemini-judge-test",
                input_tokens=120,
                output_tokens=80,
                generation_time_ms=20,
            )

    monkeypatch.setattr("app.routers.projects.GeminiClient", FakeGeminiJudgeClient)

    client, db_factory = client_and_db
    create_user(db_factory, "admin@example.com", "admin")
    create_user(db_factory, "viewer@example.com", "viewer")
    admin_token = login(client, "admin@example.com")
    viewer_token = login(client, "viewer@example.com")
    graph = create_setup_graph(client, admin_token, "Automated CLEAR-RAG Scoring")

    no_answers = client.post(
        f"/projects/{graph['project_id']}/runs/{graph['run_id']}/auto-evaluate",
        headers=auth_headers(admin_token),
    )
    assert no_answers.status_code == 422

    chunk_path = (
        f"/projects/{graph['project_id']}/runs/{graph['run_id']}"
        f"/questions/{graph['question_id']}/retrieved-chunks"
    )
    chunk = client.post(
        chunk_path,
        json={
            "source_document_id": graph["document_id"],
            "rank": 1,
            "chunk_text": "Full-time employees receive 20 days of annual leave after one year.",
            "section_reference": "Section 3.1",
            "relevance_label": "high",
            "retrieval_time_ms": 12,
        },
        headers=auth_headers(admin_token),
    )
    assert chunk.status_code == 201, chunk.text

    answer_path = (
        f"/projects/{graph['project_id']}/runs/{graph['run_id']}"
        f"/questions/{graph['question_id']}/generated-answers"
    )
    answer = client.post(
        answer_path,
        json={
            "answer_text": "Full-time employees receive 20 days of annual leave after one year. [1]",
            "model_name": "gemini-test",
            "input_tokens": 100,
            "output_tokens": 20,
            "generation_time_ms": 900,
            "estimated_cost": "0.000000",
        },
        headers=auth_headers(admin_token),
    )
    assert answer.status_code == 201, answer.text

    viewer_auto_eval = client.post(
        f"/projects/{graph['project_id']}/runs/{graph['run_id']}/auto-evaluate",
        headers=auth_headers(viewer_token),
    )
    assert viewer_auto_eval.status_code == 403

    auto_eval = client.post(
        f"/projects/{graph['project_id']}/runs/{graph['run_id']}/auto-evaluate",
        headers=auth_headers(admin_token),
    )
    assert auto_eval.status_code == 200, auto_eval.text
    auto_eval_payload = auto_eval.json()
    assert auto_eval_payload["evaluated_answers"] == 1
    assert auto_eval_payload["skipped_answers"] == 0
    assert auto_eval_payload["judge_model_name"] == "gemini-judge-test"

    evaluations = client.get(
        f"/projects/{graph['project_id']}/runs/{graph['run_id']}/evaluations",
        headers=auth_headers(viewer_token),
    )
    assert evaluations.status_code == 200, evaluations.text
    payload = evaluations.json()
    assert len(payload) == 1
    assert payload[0]["evaluation_mode"] == "automated"
    assert payload[0]["overall_score"] == "4.60"
    assert payload[0]["judge_model_name"] == "gemini-judge-test"
    assert payload[0]["judge_reasoning"] == "The answer directly uses the retrieved annual leave evidence."

    repeat_auto_eval = client.post(
        f"/projects/{graph['project_id']}/runs/{graph['run_id']}/auto-evaluate",
        headers=auth_headers(admin_token),
    )
    assert repeat_auto_eval.status_code == 200
    repeated_evaluations = client.get(
        f"/projects/{graph['project_id']}/runs/{graph['run_id']}/evaluations",
        headers=auth_headers(viewer_token),
    )
    assert repeated_evaluations.status_code == 200
    assert len(repeated_evaluations.json()) == 1


def test_run_comparison_summarizes_experiment_deltas(
    client_and_db: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, db_factory = client_and_db
    create_user(db_factory, "admin@example.com", "admin")
    create_user(db_factory, "viewer@example.com", "viewer")
    admin_token = login(client, "admin@example.com")
    viewer_token = login(client, "viewer@example.com")
    graph = create_setup_graph(client, admin_token, "Run Comparison")

    second_run = client.post(
        f"/projects/{graph['project_id']}/runs",
        json={"name": "Vector Evaluation", "system_version": "v2", "notes": "Vector retrieval run"},
        headers=auth_headers(admin_token),
    )
    assert second_run.status_code == 201, second_run.text
    second_run_id = second_run.json()["id"]

    with db_factory() as db:
        baseline = db.get(EvaluationRun, graph["run_id"])
        vector = db.get(EvaluationRun, second_run_id)
        assert baseline is not None
        assert vector is not None
        baseline.retrieval_mode = "keyword"
        baseline.generator_model_name = "gemini-test"
        vector.retrieval_mode = "vector"
        vector.generator_model_name = "gemini-test"
        vector.embedding_model_name = "gemini-embedding-001"
        vector.judge_model_name = "gemini-judge-test"
        db.commit()

    for run_id, answer_text, scores in [
        (
            graph["run_id"],
            "Employees receive 20 days of annual leave after one year.",
            {
                "citation_quality_score": 4,
                "latency_cost_score": 4,
                "evidence_faithfulness_score": 4,
                "answer_relevance_score": 4,
                "retrieval_quality_score": 4,
            },
        ),
        (
            second_run_id,
            "Employees receive 20 days of annual leave after one year. [1]",
            {
                "citation_quality_score": 5,
                "latency_cost_score": 4,
                "evidence_faithfulness_score": 5,
                "answer_relevance_score": 5,
                "retrieval_quality_score": 5,
            },
        ),
    ]:
        answer = client.post(
            f"/projects/{graph['project_id']}/runs/{run_id}/questions/{graph['question_id']}/generated-answers",
            json={
                "answer_text": answer_text,
                "model_name": "gemini-test",
                "input_tokens": 100,
                "output_tokens": 20,
                "generation_time_ms": 900,
                "estimated_cost": "0.000000",
            },
            headers=auth_headers(admin_token),
        )
        assert answer.status_code == 201, answer.text
        evaluation = client.post(
            f"/projects/{graph['project_id']}/runs/{run_id}/questions/{graph['question_id']}/answers/{answer.json()['id']}/evaluations",
            json={
                **scores,
                "reviewer_notes": "Comparison score.",
                "suggested_improvement": "Keep testing.",
            },
            headers=auth_headers(admin_token),
        )
        assert evaluation.status_code == 201, evaluation.text

    viewer_compare = client.get(
        f"/projects/{graph['project_id']}/runs/compare",
        params=[("run_ids", graph["run_id"]), ("run_ids", second_run_id)],
        headers=auth_headers(viewer_token),
    )
    assert viewer_compare.status_code == 200, viewer_compare.text
    payload = viewer_compare.json()
    assert payload["baseline_run_id"] == graph["run_id"]
    assert payload["compared_run_ids"] == [graph["run_id"], second_run_id]
    assert payload["runs"][0]["retrieval_mode"] == "keyword"
    assert payload["runs"][1]["retrieval_mode"] == "vector"
    assert payload["runs"][1]["embedding_model_name"] == "gemini-embedding-001"
    assert payload["runs"][0]["average_overall_score"] == "4.00"
    assert payload["runs"][1]["average_overall_score"] == "4.80"
    assert payload["metric_deltas"][str(second_run_id)]["overall_score_delta"] == "0.80"
    assert payload["metric_deltas"][str(second_run_id)]["retrieval_quality_delta"] == "1.00"
    assert payload["question_results"][0]["best_run_id"] == second_run_id

    duplicate_compare = client.get(
        f"/projects/{graph['project_id']}/runs/compare",
        params=[("run_ids", graph["run_id"]), ("run_ids", graph["run_id"])],
        headers=auth_headers(admin_token),
    )
    assert duplicate_compare.status_code == 422

    missing_compare = client.get(
        f"/projects/{graph['project_id']}/runs/compare",
        params=[("run_ids", graph["run_id"]), ("run_ids", 999999)],
        headers=auth_headers(admin_token),
    )
    assert missing_compare.status_code == 404


def test_question_dataset_import_csv_json_validation_and_role_access(
    client_and_db: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, db_factory = client_and_db
    create_user(db_factory, "admin@example.com", "admin")
    create_user(db_factory, "viewer@example.com", "viewer")
    admin_token = login(client, "admin@example.com")
    viewer_token = login(client, "viewer@example.com")
    graph = create_setup_graph(client, admin_token, "Question Dataset Import")

    csv_content = (
        "question_text,question_type,expected_source\n"
        "How many annual leave days does an employee receive after one year?,simple_factual,HR Leave Policy\n"
        "When is a medical certificate required?,conditional,HR Leave Policy\n"
        "When is a medical certificate required?,conditional,HR Leave Policy\n"
        "Which policy is invalid?,wrong_type,HR Leave Policy\n"
        ",simple_factual,HR Leave Policy\n"
    )

    viewer_import = client.post(
        f"/projects/{graph['project_id']}/question-datasets/import",
        data={"dataset_name": "Viewer Import", "dataset_version": "v1"},
        files={"file": ("questions.csv", csv_content.encode("utf-8"), "text/csv")},
        headers=auth_headers(viewer_token),
    )
    assert viewer_import.status_code == 403

    imported = client.post(
        f"/projects/{graph['project_id']}/question-datasets/import",
        data={"dataset_name": "HR Regression Set", "dataset_version": "v1"},
        files={"file": ("questions.csv", csv_content.encode("utf-8"), "text/csv")},
        headers=auth_headers(admin_token),
    )
    assert imported.status_code == 201, imported.text
    payload = imported.json()
    assert payload["dataset"]["dataset_name"] == "HR Regression Set"
    assert payload["dataset"]["question_count"] == 1
    assert payload["questions_imported"] == 1
    assert payload["duplicate_questions"] == 2
    assert payload["invalid_rows"] == 2
    assert payload["errors"][0]["row_number"] == 5

    datasets = client.get(
        f"/projects/{graph['project_id']}/question-datasets",
        headers=auth_headers(viewer_token),
    )
    assert datasets.status_code == 200, datasets.text
    assert len(datasets.json()) == 1
    assert datasets.json()[0]["question_count"] == 1

    questions = client.get(
        f"/projects/{graph['project_id']}/questions",
        headers=auth_headers(viewer_token),
    )
    assert questions.status_code == 200, questions.text
    imported_questions = [question for question in questions.json() if question["dataset_id"] == payload["dataset"]["id"]]
    assert len(imported_questions) == 1
    assert imported_questions[0]["question_text"] == "When is a medical certificate required?"

    json_content = b'{"questions":[{"question_text":"How much annual leave can be carried forward?","question_type":"simple_factual","expected_source":"HR Leave Policy"}]}'
    json_import = client.post(
        f"/projects/{graph['project_id']}/question-datasets/import",
        data={"dataset_name": "HR JSON Set", "dataset_version": "v2"},
        files={"file": ("questions.json", json_content, "application/json")},
        headers=auth_headers(admin_token),
    )
    assert json_import.status_code == 201, json_import.text
    assert json_import.json()["questions_imported"] == 1

    unsupported = client.post(
        f"/projects/{graph['project_id']}/question-datasets/import",
        data={"dataset_name": "Bad Set"},
        files={"file": ("questions.txt", b"question", "text/plain")},
        headers=auth_headers(admin_token),
    )
    assert unsupported.status_code == 422

    missing_columns = client.post(
        f"/projects/{graph['project_id']}/question-datasets/import",
        data={"dataset_name": "Missing Columns"},
        files={"file": ("bad.csv", b"question_text\nOnly one column", "text/csv")},
        headers=auth_headers(admin_token),
    )
    assert missing_columns.status_code == 422
