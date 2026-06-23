"""
TaskInstance service — basic CRUD and status updates for instances.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.exceptions import NotFoundError
from app.models.task_instance import TaskInstance
from app.repositories.task_instance import TaskInstanceRepository
from app.schemas.task_instance import TaskInstanceUpdate


class TaskInstanceService:
    """Business logic for interacting with individual task instances."""

    def __init__(self, db: Session) -> None:
        self.repo = TaskInstanceRepository(db)
        self.db = db

    def get_by_date(self, target_date: date) -> list[TaskInstance]:
        """Fetch all instances for a specific date."""
        return self.repo.get_by_date_range(target_date, target_date)

    def get_by_id(self, instance_id: str) -> TaskInstance:
        """Fetch a single instance or raise NotFoundError."""
        instance = self.repo.get_by_id(instance_id)
        if not instance:
            raise NotFoundError("TaskInstance", instance_id)
        return instance

    def update_status(self, instance_id: str, data: TaskInstanceUpdate) -> TaskInstance:
        """Update the status of an instance."""
        instance = self.get_by_id(instance_id)

        if data.status != instance.status:
            self.repo.update(instance, status=data.status.value)
            self.db.commit()

        return instance
