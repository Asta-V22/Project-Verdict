"""
Pydantic schemas for Task Instance operations.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.enums import InstanceStatus
from app.schemas.evidence import EvidenceResponse
from app.schemas.task import TaskResponse


class TaskInstanceUpdate(BaseModel):
    """Schema for updating a task instance status."""

    status: InstanceStatus


class SyncInstancesResponse(BaseModel):
    """Response payload when triggering instance generation."""

    generated_count: int
    synced_up_to: str
    truncation_occurred: bool


class TaskInstanceResponse(BaseModel):
    """Serialized task instance for API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    task_id: str
    task: TaskResponse | None = None
    evidence: list[EvidenceResponse] = []
    instance_date: str
    status: str
    due_time: str | None
    completed_at: str | None

    @field_validator("instance_date", "completed_at", mode="before")
    @classmethod
    def serialize_datetime(cls, v):
        """Convert date/datetime to ISO string."""
        if hasattr(v, "isoformat"):
            return v.isoformat()
        return v
