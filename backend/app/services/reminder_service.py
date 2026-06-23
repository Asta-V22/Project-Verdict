"""
Reminder service — business logic for CRUD operations.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.exceptions import NotFoundError
from app.models.reminder import Reminder
from app.repositories.reminder import ReminderRepository
from app.repositories.task import TaskRepository
from app.schemas.reminder import ReminderCreate, ReminderUpdate


class ReminderService:
    """Business logic for reminder CRUD and lookup."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ReminderRepository(db)
        self.task_repo = TaskRepository(db)

    def create_reminder(self, data: ReminderCreate) -> Reminder:
        """Create a new reminder (global or task-specific)."""
        if data.task_id:
            task = self.task_repo.get_by_id(data.task_id)
            if not task:
                raise NotFoundError("Task", data.task_id)

        reminder = Reminder(
            task_id=data.task_id,
            reminder_time=data.reminder_time,
            urgency_level=data.urgency_level.value,
        )
        self.repo.create(reminder)
        self.db.commit()
        return reminder

    def get_reminder(self, reminder_id: str) -> Reminder:
        """Fetch a single reminder by ID."""
        reminder = self.repo.get_by_id(reminder_id)
        if not reminder:
            raise NotFoundError("Reminder", reminder_id)
        return reminder

    def list_all(self) -> list[Reminder]:
        """Fetch all reminders."""
        return self.repo.get_all()

    def get_by_task(self, task_id: str) -> list[Reminder]:
        """Fetch reminders for a specific task."""
        return self.repo.get_all(task_id=task_id)

    def update_reminder(self, reminder_id: str, data: ReminderUpdate) -> Reminder:
        """Update fields on a reminder."""
        reminder = self.get_reminder(reminder_id)
        update_data = data.model_dump(exclude_unset=True)

        # Convert Enum values to string for model mapping if needed
        if "urgency_level" in update_data and update_data["urgency_level"] is not None:
            update_data["urgency_level"] = update_data["urgency_level"].value

        self.repo.update(reminder, **update_data)
        self.db.commit()
        return reminder

    def delete_reminder(self, reminder_id: str) -> None:
        """Permanently delete a reminder."""
        reminder = self.get_reminder(reminder_id)
        self.repo.hard_delete(reminder)
        self.db.commit()

    def get_due_reminders(self) -> list[Reminder]:
        """
        Fetch all active reminders that are due at the CURRENT minute.
        Checks HH:MM.
        """
        now_time = datetime.now().strftime("%H:%M")
        return self.repo.get_all(is_active=True, reminder_time=now_time)
