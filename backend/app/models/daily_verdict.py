"""
DailyVerdict model — daily summary of accountability performance.

Added now even though only `completion_rate` will be populated in Phase 1.
The `verdict_text` field is reserved for AI-generated prosecutor reports
in future phases. The table is unique on `date` — one verdict per day.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, FullTimestampMixin, generate_uuid


class DailyVerdict(FullTimestampMixin, Base):
    __tablename__ = "daily_verdicts"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    date: Mapped[date] = mapped_column(Date, unique=True, nullable=False)

    # ── Summary stats ─────────────────────────────────────────────────
    total_tasks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed_tasks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completion_rate: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False
    )  # 0.0 to 1.0

    # ── AI verdict (future) ───────────────────────────────────────────
    verdict_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        pct = f"{self.completion_rate * 100:.0f}%"
        return f"<DailyVerdict(date={self.date}, rate={pct})>"
