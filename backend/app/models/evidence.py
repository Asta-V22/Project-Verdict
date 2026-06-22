"""
Evidence model — proof that work was done.

Supports text, links, screenshots, and file attachments.

Evidence cleanup policy:
  - Users can delete the *file* while preserving the metadata record.
  - `file_deleted` / `file_deleted_at` track whether the physical file
    has been removed from disk.
  - Metadata (task reference, date, type, notes) is always preserved.
  - Future: configurable auto-cleanup (30/90/180 days or never).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, generate_uuid, utcnow


class Evidence(Base):
    __tablename__ = "evidence"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    instance_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("task_instances.id"), nullable=False, index=True
    )

    # ── What was submitted ────────────────────────────────────────────
    evidence_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # text | link | screenshot | file
    content: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # Text content or URL
    file_path: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )  # Relative path from evidence root
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_size: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )  # Bytes
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── File cleanup tracking ─────────────────────────────────────────
    file_deleted: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    file_deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )

    # ── Timestamps ────────────────────────────────────────────────────
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, nullable=False
    )

    # ── Relationships ─────────────────────────────────────────────────
    instance: Mapped[TaskInstance] = relationship(  # noqa: F821
        "TaskInstance", back_populates="evidence"
    )

    def __repr__(self) -> str:
        return (
            f"<Evidence(type={self.evidence_type!r}, "
            f"instance_id={self.instance_id!r})>"
        )
