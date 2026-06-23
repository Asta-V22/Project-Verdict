"""
Category repository — data access for categories.

Extends BaseRepository with category-specific queries.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.category import Category
from app.repositories.base import BaseRepository


class CategoryRepository(BaseRepository[Category]):
    """Category-specific data access."""

    def __init__(self, session: Session) -> None:
        super().__init__(Category, session)

    def get_by_name(self, name: str) -> Category | None:
        """Find a category by its unique name (case-insensitive)."""
        return self.get_one(name=name)

    def get_active(self) -> list[Category]:
        """Return all non-archived categories."""
        return self.get_all(is_active=True)
