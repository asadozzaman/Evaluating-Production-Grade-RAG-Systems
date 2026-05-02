from collections.abc import Generator
from pathlib import Path
import shutil

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import EvaluationRun, Role, SourceDocument, TestQuestion as QuestionModel, User
from app.security import hash_password
from app.config import get_settings


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
        shutil.rmtree(tmp_path / "uploads", ignore_errors=True)


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
    response = client.post(
        "/auth/login",
        json={"email": email, "password": "StrongPass123!"},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def create_project(client: TestClient, token: str) -> dict:
    response = client.post(
        "/projects",
        json={
            "name": "HR Policy RAG Assistant",
            "description": "Setup workspace for HR policy evaluation.",
            "system_type": "internal_knowledge_assistant",
            "target_users": "Employees",
        },
        headers=auth_headers(token),
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_project_setup_crud_and_role_access(client_and_db: tuple[TestClient, sessionmaker[Session]]) -> None:
    client, db_factory = client_and_db
    create_user(db_factory, "admin@example.com", "admin")
    create_user(db_factory, "evaluator@example.com", "evaluator")
    create_user(db_factory, "viewer@example.com", "viewer")

    admin_token = login(client, "admin@example.com")
    evaluator_token = login(client, "evaluator@example.com")
    viewer_token = login(client, "viewer@example.com")

    unauthenticated = client.get("/projects")
    assert unauthenticated.status_code == 401

    project = create_project(client, admin_token)
    project_id = project["id"]

    viewer_create = client.post(
        "/projects",
        json={
            "name": "Viewer Project",
            "system_type": "internal_knowledge_assistant",
            "target_users": "Employees",
        },
        headers=auth_headers(viewer_token),
    )
    assert viewer_create.status_code == 403

    viewer_list = client.get("/projects", headers=auth_headers(viewer_token))
    assert viewer_list.status_code == 200
    assert len(viewer_list.json()) == 1

    updated_project = client.patch(
        f"/projects/{project_id}",
        json={"name": "Updated HR Policy RAG Assistant"},
        headers=auth_headers(evaluator_token),
    )
    assert updated_project.status_code == 200
    assert updated_project.json()["name"] == "Updated HR Policy RAG Assistant"

    document = client.post(
        f"/projects/{project_id}/documents",
        json={
            "title": "HR Leave Policy",
            "document_type": "policy",
            "source_kind": "uri",
            "source_uri": "s3://example/hr-leave-policy.pdf",
            "version": "v1",
        },
        headers=auth_headers(evaluator_token),
    )
    assert document.status_code == 201, document.text
    assert document.json()["source_kind"] == "uri"
    document_id = document.json()["id"]

    uri_without_source = client.post(
        f"/projects/{project_id}/documents",
        json={
            "title": "Broken URI Document",
            "document_type": "policy",
            "source_kind": "uri",
        },
        headers=auth_headers(evaluator_token),
    )
    assert uri_without_source.status_code == 422

    uploaded_document = client.post(
        f"/projects/{project_id}/documents/upload",
        data={
            "title": "Uploaded HR Policy",
            "document_type": "policy",
            "version": "v2",
        },
        files={"file": ("hr-policy.txt", b"Employees receive 20 days of annual leave.", "text/plain")},
        headers=auth_headers(evaluator_token),
    )
    assert uploaded_document.status_code == 201, uploaded_document.text
    uploaded_payload = uploaded_document.json()
    assert uploaded_payload["source_kind"] == "file"
    assert uploaded_payload["source_uri"] is None
    assert uploaded_payload["original_file_name"] == "hr-policy.txt"
    assert uploaded_payload["file_size_bytes"] > 0
    assert uploaded_payload["storage_path"].startswith(f"documents/{project_id}/")
    uploaded_path = Path(get_settings().upload_dir) / uploaded_payload["storage_path"]
    assert uploaded_path.is_file()

    viewer_upload = client.post(
        f"/projects/{project_id}/documents/upload",
        data={"title": "Viewer Upload", "document_type": "policy"},
        files={"file": ("viewer.txt", b"Viewer cannot upload.", "text/plain")},
        headers=auth_headers(viewer_token),
    )
    assert viewer_upload.status_code == 403

    question = client.post(
        f"/projects/{project_id}/questions",
        json={
            "question_text": "How many annual leave days does an employee receive after one year?",
            "question_type": "simple_factual",
            "expected_source": "HR Leave Policy, Section 1.1",
        },
        headers=auth_headers(evaluator_token),
    )
    assert question.status_code == 201, question.text
    question_id = question.json()["id"]

    invalid_question = client.post(
        f"/projects/{project_id}/questions",
        json={
            "question_text": "Invalid question type",
            "question_type": "unsupported",
        },
        headers=auth_headers(evaluator_token),
    )
    assert invalid_question.status_code == 422

    run = client.post(
        f"/projects/{project_id}/runs",
        json={
            "name": "Baseline Evaluation",
            "system_version": "v1",
            "notes": "Basic vector search and simple prompt.",
        },
        headers=auth_headers(evaluator_token),
    )
    assert run.status_code == 201, run.text
    run_id = run.json()["id"]

    assert client.get(f"/projects/{project_id}/documents/{document_id}", headers=auth_headers(viewer_token)).status_code == 200
    assert client.get(f"/projects/{project_id}/questions/{question_id}", headers=auth_headers(viewer_token)).status_code == 200
    assert client.get(f"/projects/{project_id}/runs/{run_id}", headers=auth_headers(viewer_token)).status_code == 200

    invalid_project_document = client.post(
        "/projects/9999/documents",
        json={
            "title": "Missing Project Doc",
            "document_type": "policy",
            "source_kind": "uri",
            "source_uri": "memory://missing-project-doc",
        },
        headers=auth_headers(evaluator_token),
    )
    assert invalid_project_document.status_code == 404

    delete_project = client.delete(f"/projects/{project_id}", headers=auth_headers(admin_token))
    assert delete_project.status_code == 204

    with db_factory() as db:
        assert db.scalar(select(SourceDocument).where(SourceDocument.id == document_id)) is None
        assert db.scalar(select(QuestionModel).where(QuestionModel.id == question_id)) is None
        assert db.scalar(select(EvaluationRun).where(EvaluationRun.id == run_id)) is None
    assert not uploaded_path.exists()
