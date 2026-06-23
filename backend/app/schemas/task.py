"""
Pydantic schemas for Task CRUD operations.

Schemas:
  TaskCreate  — POST body
  TaskUpdate  — PATCH body (all fields optional)
  TaskResponse — serialized output for API responses
"""

from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.enums import EvidenceMode, RecurrenceType
from app.schemas.category import CategoryResponse


class TaskCreate(BaseModel):
    """Schema for creating a new task."""

    title: str
    description: str | None = None
    category_id: str | None = None
    recurrence: RecurrenceType = RecurrenceType.NONE
    recurrence_days: str | None = None
    evidence_mode: EvidenceMode = EvidenceMode.MIXED
    due_time: str | None = None

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Task title must not be empty")
        if len(v) > 200:
            raise ValueError("Task title must be 200 characters or fewer")
        return v

    @field_validator("due_time")
    @classmethod
    def valid_due_time(cls, v: str | None) -> str | None:
        if v is not None and not re.match(r"^([01]\d|2[0-3]):([0-5]\d)$", v):
            raise ValueError("Due time must be in HH:MM format (e.g. '19:00')")
        return v


class TaskUpdate(BaseModel):
    """Schema for updating an existing task. All fields are optional."""

    title: str | None = None
    description: str | None = None
    category_id: str | None = None
    recurrence: RecurrenceType | None = None
    recurrence_days: str | None = None
    evidence_mode: EvidenceMode | None = None
    due_time: str | None = None

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Task title must not be empty")
            if len(v) > 200:
                raise ValueError("Task title must be 200 characters or fewer")
        return v

    @field_validator("due_time")
    @classmethod
    def valid_due_time(cls, v: str | None) -> str | None:
        if v is not None and not re.match(r"^([01]\d|2[0-3]):([0-5]\d)$", v):
            raise ValueError("Due time must be in HH:MM format (e.g. '19:00')")
        return v


class TaskResponse(BaseModel):
    """Serialized task for API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    description: str | None
    category_id: str | None
    category: CategoryResponse | None = None
    recurrence: str
    recurrence_days: str | None
    evidence_mode: str
    due_time: str | None
    is_active: bool
    created_at: str
    updated_at: str | None

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def serialize_datetime(cls, v):
        """Convert datetime to ISO string if it's a datetime object."""
        if hasattr(v, "isoformat"):
            return v.isoformat()
        return v
