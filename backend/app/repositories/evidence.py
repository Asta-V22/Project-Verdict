"""
Evidence repository — data access for evidence submissions.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.evidence import Evidence
from app.repositories.base import BaseRepository


class EvidenceRepository(BaseRepository[Evidence]):
    """Evidence-specific data access."""

    def __init__(self, session: Session) -> None:
        super().__init__(Evidence, session)
