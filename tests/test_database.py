"""
Tests SQLite transaction boundaries and rollbacks.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import DBTaskRecord


@pytest.fixture
def db_session():
    """Provide an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()

    try:
        yield session
    finally:
        session.close()


def test_database_rollback(db_session):
    """Verify rollback() discards uncommitted changes."""
    task = DBTaskRecord(
        id="TASK-0001",
        sourceType="finding",
        domain="test",
        title="Test",
        priority="P1",
        approvalState="pending_review",
        executionState="not_started",
        owner="test",
        raw_payload={}
    )
    db_session.add(task)
    db_session.flush()

    db_session.rollback()

    result = db_session.query(DBTaskRecord).filter_by(id="TASK-0001").first()
    assert result is None
