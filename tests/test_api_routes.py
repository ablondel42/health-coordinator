"""
Tests for FastAPI routes.

Verifies schema validation and HTTP response handling.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, engine, get_db_session

client = TestClient(app)

TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db_session():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db_session] = override_get_db_session


@pytest.fixture(autouse=True)
def setup_db():
    """Create tables before each test, drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_health_endpoint():
    """Verify the health endpoint returns OK."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_task_rejects_invalid_schema():
    """Verify Pydantic rejects unknown fields with 422."""
    invalid_payload = {
        "id": "TASK-100",
        "hallucinated_field": True,
        "title": "Invalid Task"
    }

    response = client.post("/tasks", json=invalid_payload)
    assert response.status_code == 422


def test_start_audit_swarm():
    """Verify the audit swarm endpoint returns a run ID."""
    response = client.post("/runs")
    assert response.status_code == 200
    assert "runId" in response.json()
