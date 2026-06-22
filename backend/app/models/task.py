"""
Task model — the master definition of what a user wants to accomplish.

Key design decisions:
  - `evidence_mode` replaces the over-engineered JSON `evidence_requirements`.
    A simple enum (none/text/link/file/mixed) is sufficient for Phase 1.
  - `due_time` (HH:MM) lets the future prosecutor track on-time vs late completion.
  - Soft-delete only: `is_active=False` archives a task, preserving all
    historical data (streaks, evidence, reliability metrics).
  - `recurrence_days` is a JSON-encoded list of weekday ints (0=Mon .. 6=Sun)
    used only when `recurrence == 'custom'`.
"""

from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, FullTimestampMixin, generate_uuid
from app.models.enums import EvidenceMode, RecurrenceType


class Task(FullTimestampMixin, Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("categories.id"), nullable=True
    )
    recurrence: Mapped[str] = mapped_column(
        String(20), default=RecurrenceType.NONE.value, nullable=False
    )
    recurrence_days: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # JSON array, e.g. "[0, 2, 4]" for Mon/Wed/Fri
    evidence_mode: Mapped[str] = mapped_column(
        String(20), default=EvidenceMode.MIXED.value, nullable=False
    )
    due_time: Mapped[str | None] = mapped_column(
        String(5), nullable=True
    )  # "HH:MM" format, e.g. "19:00"
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # ── Relationships ─────────────────────────────────────────────────
    category: Mapped[Category | None] = relationship(  # noqa: F821
        "Category", back_populates="tasks", lazy="joined"
    )
    instances: Mapped[list[TaskInstance]] = relationship(  # noqa: F821
        "TaskInstance", back_populates="task", lazy="select"
    )
    reminders: Mapped[list[Reminder]] = relationship(  # noqa: F821
        "Reminder", back_populates="task", lazy="select"
    )
    metrics: Mapped[TaskMetrics | None] = relationship(  # noqa: F821
        "TaskMetrics", back_populates="task", uselist=False, lazy="joined"
    )

    def __repr__(self) -> str:
        return f"<Task(title={self.title!r}, recurrence={self.recurrence!r})>"
