"""
Shared test fixtures for the Project Verdict backend.

Provides:
  - ``test_engine``  — in-memory SQLite engine (session-scoped)
  - ``db_session``   — database session with automatic rollback per test
  - ``client``       — FastAPI TestClient wired to the test database

All tests run against an isolated in-memory database.  Each test gets
a transactional session that is rolled back after the test completes,
so tests never pollute each other.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from app.database import get_db
from app.main import create_app
from app.models.base import Base


@pytest.fixture(scope="session")
def test_engine():
    """In-memory SQLite engine shared across all tests in the session."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def _set_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.close()

    # Create all tables once
    Base.metadata.create_all(bind=engine)

    yield engine

    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(test_engine):
    """
    Per-test database session with automatic rollback.

    Uses a nested transaction so each test sees a clean state
    without needing to drop/recreate tables.
    """
    connection = test_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    """
    FastAPI TestClient wired to the in-memory test database.

    Overrides the ``get_db`` dependency so all route handlers
    use the test session instead of the production database.
    """
    app = create_app()

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app) as test_client:
        yield test_client
