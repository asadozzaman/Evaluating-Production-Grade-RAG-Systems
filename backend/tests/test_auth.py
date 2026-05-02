from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import Role


@pytest.fixture()
def client() -> Generator[TestClient]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    with TestingSessionLocal() as db:
        db.add_all(
            [
                Role(name="admin", description="Manages users, roles, and system settings."),
                Role(name="evaluator", description="Reviews RAG outputs and assigns scores."),
                Role(name="viewer", description="Views projects and results without editing."),
            ]
        )
        db.commit()

    def override_get_db() -> Generator[Session]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)


def test_authentication_and_role_access(client: TestClient) -> None:
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["llm_provider"] == "gemini"
    assert "gemini_api_key" not in health.json()

    unauthenticated = client.get("/auth/me")
    assert unauthenticated.status_code == 401

    first_user = client.post(
        "/auth/register",
        json={
            "email": "admin@example.com",
            "full_name": "Admin User",
            "password": "StrongPass123!",
        },
    )
    assert first_user.status_code == 201
    first_user_payload = first_user.json()
    assert first_user_payload["user"]["roles"][0]["name"] == "admin"

    admin_token = first_user_payload["access_token"]
    admin_check = client.get("/auth/admin-check", headers={"Authorization": f"Bearer {admin_token}"})
    assert admin_check.status_code == 200

    second_user = client.post(
        "/auth/register",
        json={
            "email": "viewer@example.com",
            "full_name": "Viewer User",
            "password": "StrongPass123!",
        },
    )
    assert second_user.status_code == 201
    second_user_payload = second_user.json()
    assert second_user_payload["user"]["roles"][0]["name"] == "viewer"

    viewer_token = second_user_payload["access_token"]
    viewer_me = client.get("/auth/me", headers={"Authorization": f"Bearer {viewer_token}"})
    assert viewer_me.status_code == 200
    assert viewer_me.json()["email"] == "viewer@example.com"

    viewer_admin_check = client.get(
        "/auth/admin-check",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert viewer_admin_check.status_code == 403

    login = client.post(
        "/auth/login",
        json={"email": "viewer@example.com", "password": "StrongPass123!"},
    )
    assert login.status_code == 200

    bad_login = client.post(
        "/auth/login",
        json={"email": "viewer@example.com", "password": "wrongpass"},
    )
    assert bad_login.status_code == 401
