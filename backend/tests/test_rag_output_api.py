from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import Role, User
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
