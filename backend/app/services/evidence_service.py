"""
Evidence service — handles file validation, storage, and instance status transitions.
"""

from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import IO

from sqlalchemy.orm import Session

from app.config import settings
from app.core.storage import StorageProvider
from app.exceptions import NotFoundError, ValidationError
from app.models.base import utcnow
from app.models.enums import EvidenceType, InstanceStatus
from app.models.evidence import Evidence
from app.repositories.evidence import EvidenceRepository
from app.repositories.task_instance import TaskInstanceRepository
from app.utils.file_safety import sanitize_filename

logger = logging.getLogger(__name__)


class EvidenceService:
    """Business logic for evidence submission and validation."""

    def __init__(self, db: Session, storage: StorageProvider) -> None:
        self.db = db
        self.repo = EvidenceRepository(db)
        self.instance_repo = TaskInstanceRepository(db)
        self.storage = storage

    def submit_file_evidence(
        self,
        instance_id: str,
        file_obj: IO[bytes],
        original_filename: str,
        content_type: str,
        file_size: int,
        notes: str | None = None,
    ) -> Evidence:
        """
        Submit a file upload as evidence.
        Enforces size and MIME type limits.
        Transitions the parent TaskInstance to SUBMITTED.
        Rolls back the file write if the database transaction fails.
        """
        # 1. Validate instance exists
        instance = self.instance_repo.get_by_id(instance_id)
        if not instance:
            raise NotFoundError("TaskInstance", instance_id)

        if not instance.task.is_active:
            raise ValidationError("Cannot submit evidence to an archived task")

        # 2. Validate file type and size
        if content_type not in settings.allowed_evidence_mime_types:
            raise ValidationError(f"File type not allowed: {content_type}")

        if file_size <= 0 or file_size > settings.max_evidence_file_size_bytes:
            limit_mb = settings.max_evidence_file_size_mb
            raise ValidationError(f"File size must be between 1 byte and {limit_mb}MB")

        # 3. Generate safe paths and names
        safe_original = sanitize_filename(original_filename)
        # Use UUID to prevent collisions on disk
        ext = safe_original.split(".")[-1] if "." in safe_original else "bin"
        disk_filename = f"{uuid.uuid4().hex}.{ext}"

        # We group files by the task instance date and instance ID
        date_str = instance.instance_date.isoformat()
        relative_path = f"{date_str}/{instance_id}/{disk_filename}"

        # 4. Save to disk
        # Read the file bytes
        file_bytes = file_obj.read()
        self.storage.save_file(relative_path, file_bytes)

        # 5. Database Transaction
        try:
            evidence = Evidence(
                instance_id=instance_id,
                evidence_type=EvidenceType.FILE.value,
                file_path=relative_path,
                file_name=safe_original,
                file_size=file_size,
                notes=notes,
            )
            self.repo.create(evidence)

            # Idempotent status transition
            if instance.status == InstanceStatus.PENDING.value:
                instance.status = InstanceStatus.SUBMITTED.value
                instance.completed_at = utcnow()

            self.db.commit()
            return evidence

        except Exception as e:
            # 6. Cleanup file if DB commit fails
            self.db.rollback()
            logger.error(
                "Database error saving evidence, rolling back file %s. Error: %s",
                relative_path,
                e,
            )
            try:
                self.storage.delete_file(relative_path)
            except Exception as cleanup_err:
                logger.error("Failed to clean up file %s: %s", relative_path, cleanup_err)
            raise

    def get_evidence_file_path(self, evidence_id: str) -> tuple[Path, Evidence]:
        """
        Retrieve the secure physical file path and Evidence record.
        Raises NotFoundError if the record is missing or the file is deleted.
        """

        evidence = self.repo.get_by_id(evidence_id)
        if not evidence:
            raise NotFoundError("Evidence", evidence_id)

        if evidence.file_deleted or not evidence.file_path:
            raise NotFoundError("Evidence File", evidence_id)

        try:
            path = self.storage.get_file_path(evidence.file_path)
            return path, evidence
        except FileNotFoundError as err:
            # Physical file missing despite DB record
            raise NotFoundError("Physical Evidence File", evidence_id) from err
