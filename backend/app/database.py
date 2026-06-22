"""
Database engine, session factory, and initialization.

SQLite-specific pragmas are applied on every connection:
  - WAL mode  → concurrent reads during writes
  - FK checks → enforce foreign key constraints (SQLite disables them by default)
"""

from __future__ import annotations

import logging
from collections.abc import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings

logger = logging.getLogger(__name__)

# ── Engine ────────────────────────────────────────────────────────────

engine = create_engine(
    settings.db_url,
    echo=False,
    connect_args={"check_same_thread": False},  # SQLite-specific
    pool_pre_ping=True,
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragmas(dbapi_connection, connection_record):
    """Apply SQLite performance and safety pragmas on each connection."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode = WAL")
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.execute("PRAGMA busy_timeout = 5000")
    cursor.close()


# ── Session Factory ───────────────────────────────────────────────────

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a database session.

    Usage in route handlers:
        db: Session = Depends(get_db)

    The caller is responsible for committing. The session is always
    closed when the request finishes, and rolled back on exceptions.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ── Initialization ────────────────────────────────────────────────────

def init_db() -> None:
    """
    Create all tables if they don't exist.

    This uses SQLAlchemy's `create_all` for initial setup.
    Subsequent schema changes should be handled through Alembic migrations.
    """
    from app.models import Base

    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ensured at: %s", settings.db_path)


def check_db_connection() -> bool:
    """Verify database connectivity. Returns True if healthy."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        logger.exception("Database connectivity check failed")
        return False
