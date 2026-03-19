"""
Database configuration and session management for the Health Coordinator.

Sets up the SQLite database connection using SQLAlchemy.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

# Ensures sqlite can be used securely in FastAPI's async threadpool
connect_arguments = {"check_same_thread": False} if "sqlite" in settings.database_url else {}

application_database_engine = create_engine(
    settings.database_url, connect_args=connect_arguments
)

ThreadSafeDatabaseSession = sessionmaker(autocommit=False, autoflush=False, bind=application_database_engine)

Base = declarative_base()

def fetch_transactional_database_session():
    """
    Dependency generator for injecting database sessions into FastAPI routes.
    Automatically closes the session after the request finishes.
    """
    database_session = ThreadSafeDatabaseSession()
    try:
        yield database_session
    finally:
        database_session.close()
