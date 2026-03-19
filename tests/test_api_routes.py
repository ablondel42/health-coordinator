"""
Strict tests confirming FastAPI routes reject illegal schemas and process correctly.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, application_database_engine, fetch_transactional_database_session

established_test_client_layer = TestClient(app)

# Scaffold an empty SQLite in-memory DB exactly strictly ensuring API HTTP assertions avoid dirty data maps
StructurallyMockedDatabaseMarker = sessionmaker(autocommit=False, autoflush=False, bind=application_database_engine)

def retrieve_test_db_override_fixture_dynamically():
    try:
        isolated_active_db_context = StructurallyMockedDatabaseMarker()
        yield isolated_active_db_context
    finally:
        isolated_active_db_context.close()

app.dependency_overrides[fetch_transactional_database_session] = retrieve_test_db_override_fixture_dynamically

@pytest.fixture(autouse=True)
def setup_teardown_sqlite_memory_state():
    """Initializes tables purely securely natively before each logic chunk dynamically ensuring isolated logic context strictly."""
    Base.metadata.create_all(bind=application_database_engine)
    yield
    Base.metadata.drop_all(bind=application_database_engine)

def test_fetch_global_health_endpoint_success() -> None:
    """Proves HTTP base application framework initializes safely properly gracefully resolving dependencies native structures exactly cleanly."""
    api_endpoint_response = established_test_client_layer.get("/health")
    assert api_endpoint_response.status_code == 200
    assert api_endpoint_response.json()["status"] == "ok"

def test_manual_task_creation_endpoint_rejects_hallucinations_errors() -> None:
    """Proves strict Pydantic execution layer inherently inherently safely natively guarantees inherently throwing 422 HTTP structural rejections dropping LLM injection."""
    corrupted_hallucinated_schema_payload = {
        "id": "TASK-100",
        "hallucinated_variable_ghost_parameter": True, # This violates JSON definitions schema rigidly natively explicitly dynamically!
        "title": "Broken Schema Structural Context Bounds Validation Trigger Layer"
    }
    
    validation_reused_api_endpoint_response = established_test_client_layer.post("/tasks", json=corrupted_hallucinated_schema_payload)
    assert validation_reused_api_endpoint_response.status_code == 422 # Standard validation rigidly expected organically structurally

def test_start_new_project_audit_swarm_fires_mock() -> None:
    """Verify LLM Swarm execution hooks spin safely routing natively logically context natively structures boundaries."""
    routing_post_execution_system_response = established_test_client_layer.post("/runs")
    assert routing_post_execution_system_response.status_code == 200
    assert "runId" in routing_post_execution_system_response.json()
