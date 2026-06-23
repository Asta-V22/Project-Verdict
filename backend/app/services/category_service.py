"""
Category service — business logic for category management.

All validation and orchestration lives here. The router calls the service;
the service calls the repository. Exceptions raised here are caught by
global handlers and returned as standard error envelopes.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.exceptions import ConflictError, NotFoundError
from app.models.category import Category
from app.repositories.category import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryUpdate


class CategoryService:
    """Category business logic."""

    def __init__(self, db: Session) -> None:
        self.repo = CategoryRepository(db)
        self.db = db

    def create(self, data: CategoryCreate) -> Category:
        """Create a new category. Raises ConflictError if name is taken."""
        existing = self.repo.get_by_name(data.name)
        if existing:
            raise ConflictError(f"Category with name '{data.name}' already exists")

        category = Category(
            name=data.name,
            color=data.color,
            icon=data.icon,
        )
        self.repo.create(category)
        self.db.commit()
        return category

    def list_active(self) -> list[Category]:
        """Return all non-archived categories."""
        return self.repo.get_active()

    def get_by_id(self, category_id: str) -> Category:
        """Get a single category. Raises NotFoundError if missing."""
        category = self.repo.get_by_id(category_id)
        if not category:
            raise NotFoundError("Category", category_id)
        return category

    def update(self, category_id: str, data: CategoryUpdate) -> Category:
        """
        Update a category. Only provided fields are changed.
        Raises NotFoundError if missing. Raises ConflictError if new name is taken.
        """
        category = self.get_by_id(category_id)

        # Check name uniqueness if name is being changed
        if data.name is not None and data.name != category.name:
            existing = self.repo.get_by_name(data.name)
            if existing:
                raise ConflictError(f"Category with name '{data.name}' already exists")

        update_fields = data.model_dump(exclude_unset=True)
        if update_fields:
            self.repo.update(category, **update_fields)
            self.db.commit()

        return category

    def archive(self, category_id: str) -> Category:
        """Soft-delete a category. Raises NotFoundError if missing."""
        category = self.get_by_id(category_id)
        self.repo.soft_delete(category)
        self.db.commit()
        return category
