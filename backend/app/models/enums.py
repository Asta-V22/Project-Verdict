"""
Domain enumerations shared across models, schemas, and services.

All enums inherit from ``enum.StrEnum`` so they serialize cleanly
to/from JSON and are stored as plain strings in SQLite.
"""

from __future__ import annotations

import enum


class RecurrenceType(enum.StrEnum):
    """How often a task repeats."""

    NONE = "none"
    DAILY = "daily"
    WEEKDAYS = "weekdays"        # Mon-Fri
    CUSTOM = "custom"            # Specific days via recurrence_days


class InstanceStatus(enum.StrEnum):
    """
    Lifecycle states for a daily task instance.

    pending   → Created, no evidence submitted yet
    submitted → User submitted evidence (awaiting verification in future phases)
    verified  → Evidence has been verified (future: AI/manual)
    skipped   → User explicitly skipped this instance
    """

    PENDING = "pending"
    SUBMITTED = "submitted"
    VERIFIED = "verified"
    SKIPPED = "skipped"


class EvidenceType(enum.StrEnum):
    """The kind of evidence a user can submit."""

    TEXT = "text"
    LINK = "link"
    SCREENSHOT = "screenshot"
    FILE = "file"


class EvidenceMode(enum.StrEnum):
    """
    What kind of evidence a task expects.

    Simplified from the original JSON-based evidence_requirements.
    Phase 1 uses this simple enum; richer validation can be layered on later.
    """

    NONE = "none"        # No evidence required (trust-based, not recommended)
    TEXT = "text"         # Text/notes only
    LINK = "link"        # URL links
    FILE = "file"        # File uploads (screenshots, attachments)
    MIXED = "mixed"      # Any combination of the above


class UrgencyLevel(enum.StrEnum):
    """Escalating urgency for reminder notifications."""

    GENTLE = "gentle"
    MODERATE = "moderate"
    URGENT = "urgent"
