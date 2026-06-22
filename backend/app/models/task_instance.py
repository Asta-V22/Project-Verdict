"""
TaskInstance model — one row per task per day.

This is the architectural heartbeat of Project Verdict. A recurring task
doesn't "complete" — its *daily instance* does. Evidence, status, and
completion time all belong to the instance, not the master task.

Key constraints:
  - UNIQUE(task_id, instance_date) — a task can only have one instance per day.
  - `due_time` is copied from the parent task at creation time so changes to
    the task's due_time don't retroactively affect historical instances.
  - `completed_at` records when the user actually submitted evidence, enabling
    the future prosecutor to calculate lateness.
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, generate_uuid
from app.models.enums import InstanceStatus


class TaskInstance(TimestampMixin, Base):
    __tablename__ = "task_instances"
    __table_args__ = (
        UniqueConstraint("task_id", "instance_date", name="uq_task_instance_date"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    task_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("tasks.id"), nullable=False, index=True
    )
    instance_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(20), default=InstanceStatus.PENDING.value, nullable=False
    )
    due_time: Mapped[str | None] = mapped_column(
        String(5), nullable=True
    )  # "HH:MM" — snapshot from parent task at creation
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # ── Relationships ─────────────────────────────────────────────────
    task: Mapped[Task] = relationship(  # noqa: F821
        "Task", back_populates="instances", lazy="joined"
    )
    evidence: Mapped[list[Evidence]] = relationship(  # noqa: F821
        "Evidence",
        back_populates="instance",
        lazy="select",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<TaskInstance(task_id={self.task_id!r}, "
            f"date={self.instance_date}, status={self.status!r})>"
        )
