"""
Base repository — generic CRUD operations for all models.

The repository pattern separates data access from business logic. Services
call repositories; repositories call SQLAlchemy. This means:
  - Business logic is testable without a real database (mock the repo)
  - Future data sources (API, cache) can be swapped in without changing services
  - All database queries live in one predictable layer
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Generic repository providing common CRUD operations.

    Subclass this for model-specific queries. The session is injected
    per-request via FastAPI's dependency injection.
    """

    def __init__(self, model: type[ModelType], session: Session) -> None:
        self.model = model
        self.session = session

    # ── Read ──────────────────────────────────────────────────────────

    def get_by_id(self, id: str) -> ModelType | None:
        """Fetch a single record by primary key."""
        return self.session.get(self.model, id)

    def get_all(self, **filters: Any) -> list[ModelType]:
        """
        Fetch all records, optionally filtered by column values.

        Usage:
            repo.get_all(is_active=True, category_id="abc-123")
        """
        stmt = select(self.model)
        for column_name, value in filters.items():
            if hasattr(self.model, column_name):
                stmt = stmt.where(getattr(self.model, column_name) == value)
        return list(self.session.scalars(stmt).all())

    def get_one(self, **filters: Any) -> ModelType | None:
        """Fetch a single record matching the given filters."""
        stmt = select(self.model)
        for column_name, value in filters.items():
            if hasattr(self.model, column_name):
                stmt = stmt.where(getattr(self.model, column_name) == value)
        return self.session.scalars(stmt).first()

    # ── Create ────────────────────────────────────────────────────────

    def create(self, obj: ModelType) -> ModelType:
        """Add a new record. Caller must commit the session."""
        self.session.add(obj)
        self.session.flush()
        return obj

    # ── Update ────────────────────────────────────────────────────────

    def update(self, obj: ModelType, **kwargs: Any) -> ModelType:
        """
        Update specific fields on an existing record.
        Caller must commit the session.
        """
        for key, value in kwargs.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
        self.session.flush()
        return obj

    # ── Delete ────────────────────────────────────────────────────────

    def soft_delete(self, obj: ModelType) -> ModelType:
        """
        Archive a record by setting `is_active = False`.
        Raises ValueError if the model doesn't support soft delete.
        """
        if not hasattr(obj, "is_active"):
            raise ValueError(
                f"{self.model.__name__} does not support soft delete "
                f"(missing 'is_active' column)"
            )
        obj.is_active = False  # type: ignore[attr-defined]
        self.session.flush()
        return obj

    def hard_delete(self, obj: ModelType) -> None:
        """
        Permanently remove a record. Use with extreme caution.
        Most models should use `soft_delete` instead.
        """
        self.session.delete(obj)
        self.session.flush()

    # ── Utility ───────────────────────────────────────────────────────

    def count(self, **filters: Any) -> int:
        """Count records matching the given filters."""
        return len(self.get_all(**filters))

    def exists(self, **filters: Any) -> bool:
        """Check if any record matches the given filters."""
        return self.get_one(**filters) is not None
