"""
Task repository — data access for tasks.

Extends BaseRepository with task-specific queries.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.task import Task
from app.repositories.base import BaseRepository


class TaskRepository(BaseRepository[Task]):
    """Task-specific data access."""

    def __init__(self, session: Session) -> None:
        super().__init__(Task, session)

    def get_active(self) -> list[Task]:
        """Return all non-archived tasks."""
        return self.get_all(is_active=True)
