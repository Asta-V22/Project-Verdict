"""
Reminder model.

Configurable reminders attached to specific tasks or global (task_id=NULL).
The urgency level drives notification styling and escalation behavior.
"""

from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, generate_uuid
from app.models.enums import UrgencyLevel


class Reminder(TimestampMixin, Base):
    __tablename__ = "reminders"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    task_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("tasks.id"), nullable=True
    )  # NULL = global reminder for all pending tasks
    reminder_time: Mapped[str] = mapped_column(
        String(5), nullable=False
    )  # "HH:MM" format
    urgency_level: Mapped[str] = mapped_column(
        String(20), default=UrgencyLevel.GENTLE.value, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # ── Relationships ─────────────────────────────────────────────────
    task: Mapped[Task | None] = relationship(  # noqa: F821
        "Task", back_populates="reminders"
    )

    def __repr__(self) -> str:
        target = self.task_id or "global"
        return f"<Reminder(time={self.reminder_time!r}, target={target})>"
