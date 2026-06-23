"""
Pydantic schemas for Reminders.
"""

from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.enums import UrgencyLevel


class ReminderCreate(BaseModel):
    """Schema for creating a reminder."""

    task_id: str | None = None
    reminder_time: str
    urgency_level: UrgencyLevel = UrgencyLevel.GENTLE

    @field_validator("reminder_time")
    @classmethod
    def validate_time(cls, v: str) -> str:
        """Ensure time is in HH:MM format."""
        if not re.match(r"^([01]\d|2[0-3]):([0-5]\d)$", v):
            raise ValueError("Time must be in HH:MM format")
        return v


class ReminderUpdate(BaseModel):
    """Schema for updating a reminder."""

    reminder_time: str | None = None
    urgency_level: UrgencyLevel | None = None
    is_active: bool | None = None

    @field_validator("reminder_time")
    @classmethod
    def validate_time(cls, v: str | None) -> str | None:
        """Ensure time is in HH:MM format."""
        if v is not None and not re.match(r"^([01]\d|2[0-3]):([0-5]\d)$", v):
            raise ValueError("Time must be in HH:MM format")
        return v


class ReminderResponse(BaseModel):
    """Serialized reminder for API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    task_id: str | None
    reminder_time: str
    urgency_level: str
    is_active: bool
    created_at: str

    @field_validator("created_at", mode="before")
    @classmethod
    def serialize_datetime(cls, v):
        """Convert datetime to ISO string."""
        if hasattr(v, "isoformat"):
            return v.isoformat()
        return v
