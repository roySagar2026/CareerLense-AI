from __future__ import annotations

import os

# Must be set before the app (and its cached settings) is imported.
os.environ["APP_ENV"] = "test"
os.environ.setdefault("JWT_SECRET", "test-secret-test-secret-test-secret-0123456789")
os.environ["DATABASE_URL"] = os.getenv("TEST_DATABASE_URL", "sqlite://")

import pytest

from tests.synthetic import JOB_TEXT, make_docx

PASSWORD = "CareerLens-Test-9"


@pytest.fixture()
def client():
    from fastapi.testclient import TestClient

    from app.core import database
    from app.main import app
    from app.models import Base

    engine = database.configure(os.environ["DATABASE_URL"])
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with TestClient(app) as test_client:
        yield test_client
    Base.metadata.drop_all(engine)


def register(client, email: str = "asha@example.com") -> dict:
    response = client.post("/api/v1/auth/register", json={"email": email, "password": PASSWORD, "full_name": "Asha"})
    assert response.status_code == 201, response.text
    return response.json()


def auth_headers(client, email: str = "asha@example.com") -> dict:
    token = register(client, email)["access_token"]
    return {"Authorization": f"Bearer {token}"}


def upload_resume(client, headers, name: str = "My Resume", parent: str | None = None):
    data = {"name": name}
    if parent:
        data["parent_resume_id"] = parent
    files = {
        "file": (
            "resume.docx",
            make_docx(),
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    }
    return client.post("/api/v1/resumes/upload", data=data, files=files, headers=headers)


def create_job(client, headers, text: str = JOB_TEXT):
    return client.post(
        "/api/v1/jobs", json={"title": "Backend Engineer", "company": "Northwind", "raw_text": text}, headers=headers
    )
