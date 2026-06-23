"""
Reminder repository — data access for reminders.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.reminder import Reminder
from app.repositories.base import BaseRepository


class ReminderRepository(BaseRepository[Reminder]):
    """Reminder-specific data access."""

    def __init__(self, session: Session) -> None:
        super().__init__(Reminder, session)
