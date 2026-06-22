"""
TaskMetrics model — pre-computed accountability metrics per task.

This table exists to avoid expensive recalculation from historical data.
Metrics are updated incrementally as instances are completed or missed.

Includes `debt_count` for the future accountability debt mechanic:
  - Miss a day → debt increases
  - Complete a day → debt decreases (or stays at 0)
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, generate_uuid, utcnow


class TaskMetrics(Base):
    __tablename__ = "task_metrics"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    task_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("tasks.id"), unique=True, nullable=False
    )

    # ── Performance counters ──────────────────────────────────────────
    successful_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    missed_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # ── Streaks ───────────────────────────────────────────────────────
    current_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    best_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_completion_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # ── Accountability debt ───────────────────────────────────────────
    debt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # ── Timestamp ─────────────────────────────────────────────────────
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow, nullable=False
    )

    # ── Relationships ─────────────────────────────────────────────────
    task: Mapped[Task] = relationship(  # noqa: F821
        "Task", back_populates="metrics"
    )

    def __repr__(self) -> str:
        return (
            f"<TaskMetrics(task_id={self.task_id!r}, "
            f"streak={self.current_streak}, debt={self.debt_count})>"
        )
