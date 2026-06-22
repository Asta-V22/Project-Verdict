"""
SQLAlchemy declarative base and shared mixins.

All models inherit from `Base`. Timestamp mixins provide consistent
`created_at` / `updated_at` columns across all tables. UUIDs are
generated client-side as strings for maximum SQLite compatibility.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utcnow() -> datetime:
    """Timezone-aware UTC timestamp (replaces deprecated datetime.utcnow)."""
    return datetime.now(UTC)


def generate_uuid() -> str:
    """Generate a new UUID4 string for use as a primary key."""
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    """Declarative base for all Project Verdict models."""

    pass


class TimestampMixin:
    """Adds a `created_at` column (set once on insert)."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utcnow,
        nullable=False,
    )


class FullTimestampMixin(TimestampMixin):
    """Adds both `created_at` and `updated_at` columns."""

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )
