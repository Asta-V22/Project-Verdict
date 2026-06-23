"""
Task service — business logic for task management.

All validation and orchestration lives here.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.exceptions import NotFoundError
from app.models.task import Task
from app.repositories.category import CategoryRepository
from app.repositories.task import TaskRepository
from app.schemas.task import TaskCreate, TaskUpdate


class TaskService:
    """Task business logic."""

    def __init__(self, db: Session) -> None:
        self.repo = TaskRepository(db)
        self.category_repo = CategoryRepository(db)
        self.db = db

    def _validate_category(self, category_id: str | None) -> None:
        """Ensure the referenced category exists and is active."""
        if category_id is not None:
            category = self.category_repo.get_by_id(category_id)
            if not category or not category.is_active:
                raise NotFoundError("Category", category_id)

    def create(self, data: TaskCreate) -> Task:
        """Create a new task."""
        self._validate_category(data.category_id)

        task = Task(
            title=data.title,
            description=data.description,
            category_id=data.category_id,
            recurrence=data.recurrence.value,
            recurrence_days=data.recurrence_days,
            evidence_mode=data.evidence_mode.value,
            due_time=data.due_time,
        )
        self.repo.create(task)
        self.db.commit()
        return task

    def list_active(self) -> list[Task]:
        """Return all non-archived tasks."""
        return self.repo.get_active()

    def get_by_id(self, task_id: str) -> Task:
        """Get a single task. Raises NotFoundError if missing."""
        task = self.repo.get_by_id(task_id)
        if not task:
            raise NotFoundError("Task", task_id)
        return task

    def update(self, task_id: str, data: TaskUpdate) -> Task:
        """
        Update a task. Only provided fields are changed.
        Raises NotFoundError if missing or if category_id refers to a missing category.
        """
        task = self.get_by_id(task_id)

        # Check category existence if it's being updated
        if data.category_id is not None and data.category_id != task.category_id:
            self._validate_category(data.category_id)

        update_fields = data.model_dump(exclude_unset=True)
        if update_fields.get("recurrence"):
            update_fields["recurrence"] = update_fields["recurrence"].value
        if update_fields.get("evidence_mode"):
            update_fields["evidence_mode"] = update_fields["evidence_mode"].value

        if update_fields:
            self.repo.update(task, **update_fields)
            self.db.commit()

        return task

    def archive(self, task_id: str) -> Task:
        """Soft-delete a task. Raises NotFoundError if missing."""
        task = self.get_by_id(task_id)
        self.repo.soft_delete(task)
        self.db.commit()
        return task
