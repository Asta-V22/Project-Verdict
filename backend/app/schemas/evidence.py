"""
Pydantic schemas for Evidence.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, field_validator


class EvidenceResponse(BaseModel):
    """Serialized evidence for API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    instance_id: str
    evidence_type: str
    content: str | None
    file_path: str | None
    file_name: str | None
    file_size: int | None
    notes: str | None
    file_deleted: bool
    submitted_at: str

    @field_validator("submitted_at", mode="before")
    @classmethod
    def serialize_datetime(cls, v):
        """Convert datetime to ISO string."""
        if hasattr(v, "isoformat"):
            return v.isoformat()
        return v
