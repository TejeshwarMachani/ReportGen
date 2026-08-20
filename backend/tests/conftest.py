"""Pytest configuration and fixtures."""
import os
import uuid

# Set test environment variables before importing app
os.environ["DATABASE_URL"] = "sqlite:///./.test_verify.db"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["SECRET_KEY"] = "test-secret-key-for-ci-1234567890abcdef"
os.environ["ANTHROPIC_API_KEY"] = "dummy-key-for-testing"
os.environ["ENVIRONMENT"] = "testing"

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import Base, engine


@pytest.fixture(scope="session", autouse=True)
def _reset_db():
    """Create a fresh schema for the test session."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    # Leave the test db in place for inspection on failure.


@pytest.fixture()
def client():
    """Synchronous test client against the ASGI app."""
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def auth_headers(client):
    """Register a fresh user and return authenticated headers."""
    email = f"user-{uuid.uuid4().hex[:8]}@example.com"
    r = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "password123",
            "full_name": "Test User",
            "org_name": f"Org-{uuid.uuid4().hex[:6]}",
        },
    )
    assert r.status_code == 201, r.text
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def sample_dataset(client, auth_headers):
    """Upload a sample CSV dataset for a registered user."""
    import io

    csv_bytes = b"date,revenue\n2024-01,100\n2024-02,150\n2024-03,200\n"
    r = client.post(
        "/api/v1/datasets/upload",
        headers=auth_headers,
        files={"file": ("data.csv", io.BytesIO(csv_bytes), "text/csv")},
    )
    assert r.status_code == 201, r.text
    return r.json()