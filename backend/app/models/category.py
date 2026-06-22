"""
Category model.

Categories are user-defined labels for organizing tasks (e.g. "Leetcode",
"AI/ML", "Projects"). The database starts empty — no pre-seeded categories.

Categories support soft-delete (archival) to preserve historical references.
"""

from __future__ import annotations

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, generate_uuid


class Category(TimestampMixin, Base):
    __tablename__ = "categories"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    color: Mapped[str] = mapped_column(String(7), nullable=False)  # Hex: #RRGGBB
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # ── Relationships ─────────────────────────────────────────────────
    tasks: Mapped[list[Task]] = relationship(  # noqa: F821
        "Task", back_populates="category", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<Category(name={self.name!r}, color={self.color!r})>"
