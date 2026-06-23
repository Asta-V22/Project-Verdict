"""
TaskInstance repository — data access for task instances.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.task_instance import TaskInstance
from app.repositories.base import BaseRepository


class TaskInstanceRepository(BaseRepository[TaskInstance]):
    """TaskInstance-specific data access."""

    def __init__(self, session: Session) -> None:
        super().__init__(TaskInstance, session)

    def get_by_date_range(self, start_date: date, end_date: date) -> list[TaskInstance]:
        """Fetch all instances between start_date and end_date (inclusive)."""
        stmt = select(self.model).where(
            self.model.instance_date >= start_date,
            self.model.instance_date <= end_date,
        )
        return list(self.session.scalars(stmt).all())

    def get_by_task_and_date_range(
        self, task_ids: list[str], start_date: date, end_date: date
    ) -> list[TaskInstance]:
        """Fetch instances for specific tasks within a date range."""
        if not task_ids:
            return []
        stmt = select(self.model).where(
            self.model.task_id.in_(task_ids),
            self.model.instance_date >= start_date,
            self.model.instance_date <= end_date,
        )
        return list(self.session.scalars(stmt).all())
