"""
Tests SQLite database transaction boundaries and rollbacks.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import Generator

from app.database import Base
from app.models import DBTaskRecord

@pytest.fixture
def mock_transactional_database_session() -> Generator:
    """Provides a fresh, empty in-memory SQLite database for testing."""
    in_memory_sqlite_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=in_memory_sqlite_engine)
    testing_local_database_session = sessionmaker(autocommit=False, autoflush=False, bind=in_memory_sqlite_engine)
    active_session_instance = testing_local_database_session()
    
    try:
        yield active_session_instance
    finally:
        active_session_instance.close()

def test_database_rollback_on_failure(mock_transactional_database_session) -> None:
    """Ensure that if an exception occurs mid-transaction, records are safely rolled back."""
    mock_task_record = DBTaskRecord(
        id="TASK-0001", sourceType="finding", domain="test", title="Test",
        priority="P1", approvalState="pending_review", executionState="not_started",
        owner="test_runner", raw_payload={}
    )
    mock_transactional_database_session.add(mock_task_record)
    mock_transactional_database_session.flush() # Stage but don't commit
    
    # Pretend a failure happens here, inducing a rollback
    mock_transactional_database_session.rollback()
    
    verified_deleted_task = mock_transactional_database_session.query(DBTaskRecord).filter_by(id="TASK-0001").first()
    assert verified_deleted_task is None, "Database changes were committed instead of rolled back!"
