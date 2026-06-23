"""
Evidence API endpoints.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.core.storage import LocalStorageProvider, StorageProvider
from app.dependencies import get_db
from app.exceptions import ValidationError
from app.schemas.evidence import EvidenceResponse
from app.schemas.responses import SuccessResponse
from app.services.evidence_service import EvidenceService

router = APIRouter(tags=["evidence"])


def _get_storage_provider() -> StorageProvider:
    # Use LocalStorageProvider with the evidence directory
    return LocalStorageProvider(settings.evidence_dir)


def _get_evidence_service(
    db: Session = Depends(get_db),
    storage: StorageProvider = Depends(_get_storage_provider),
) -> EvidenceService:
    return EvidenceService(db, storage)


@router.post(
    "/instances/{instance_id}/evidence",
    response_model=SuccessResponse[EvidenceResponse],
    status_code=201,
)
def submit_evidence(
    instance_id: str,
    file: Annotated[UploadFile, File(...)],
    notes: Annotated[str | None, Form()] = None,
    service: EvidenceService = Depends(_get_evidence_service),
) -> dict:
    """
    Submit file evidence for a specific task instance.
    The file must be less than the configured MB limit (default 10MB)
    and match an allowed MIME type.
    """
    if not file.filename:
        raise ValidationError("Filename is missing")

    # file.size is provided by FastAPI if the spooled file is sized,
    # but to be safe we read it directly in the service or rely on size attribute.
    # UploadFile in FastAPI has a `.size` attribute (available in newer versions).
    file_size = getattr(file, "size", 0)

    # If size wasn't parsed correctly by FastAPI (e.g., testing with older clients),
    # we can determine it from the file object.
    if file_size == 0 or file_size is None:
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)     # Reset to beginning

    evidence = service.submit_file_evidence(
        instance_id=instance_id,
        file_obj=file.file,
        original_filename=file.filename,
        content_type=file.content_type or "application/octet-stream",
        file_size=file_size,
        notes=notes,
    )

    return {"success": True, "data": EvidenceResponse.model_validate(evidence)}

@router.get(
    "/evidence/{evidence_id}/file",
    status_code=200,
    responses={404: {"description": "Evidence not found"}}
)
def get_evidence_file(
    evidence_id: str,
    service: EvidenceService = Depends(_get_evidence_service),
) -> FileResponse:
    """
    Stream an evidence file directly to the client.
    Sets the Content-Disposition header to preserve the original filename.
    """
    path, evidence = service.get_evidence_file_path(evidence_id)
    return FileResponse(
        path,
        filename=evidence.file_name,
        content_disposition_type="inline"  # browser views images directly
    )
