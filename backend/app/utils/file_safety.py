"""
File safety utilities for evidence uploads.

Protects against:
  - Path traversal attacks  (../../etc/passwd)
  - Filename injection      (null bytes, special characters)
  - File size violations    (configurable limit, default 10 MB)

Created now so the security boundary exists before any file-handling
code lands in Sub-Phase 1D.
"""

from __future__ import annotations

import os
import re
import unicodedata
from pathlib import Path

from app.config import settings


def sanitize_filename(filename: str) -> str:
    """
    Clean a user-supplied filename for safe local storage.

    Strips directory components, null bytes, control characters,
    and OS-dangerous characters.  Normalizes Unicode and caps
    the length at 200 characters (preserving the extension).
    """
    # Normalize unicode
    filename = unicodedata.normalize("NFKD", filename)

    # Strip any directory path component
    filename = os.path.basename(filename)

    # Remove null bytes
    filename = filename.replace("\x00", "")

    # Replace path separators and OS-dangerous characters
    filename = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", filename)

    # Strip leading/trailing dots and spaces (Windows-unsafe)
    filename = filename.strip(". ")

    # Limit total length, preserving extension
    if len(filename) > 200:
        name, ext = os.path.splitext(filename)
        filename = name[: 200 - len(ext)] + ext

    # Fallback for completely empty result
    return filename or "unnamed_file"


def validate_file_size(size_bytes: int) -> bool:
    """Return True if ``size_bytes`` is within the configured upload limit."""
    return 0 < size_bytes <= settings.max_evidence_file_size_bytes


def safe_evidence_path(date_str: str, instance_id: str, filename: str) -> Path:
    """
    Build a sandboxed file path inside the evidence directory.

    Structure: ``evidence/{date}/{instance_id}/{sanitized_filename}``

    Raises ``ValueError`` if the resolved path would escape the
    evidence root (path traversal attempt).
    """
    safe_name = sanitize_filename(filename)
    target = settings.evidence_dir / date_str / instance_id / safe_name

    # Resolve to absolute and verify containment
    resolved = target.resolve()
    evidence_root = settings.evidence_dir.resolve()

    if not str(resolved).startswith(str(evidence_root)):
        raise ValueError(
            f"Path traversal detected: {filename!r} resolves outside evidence directory"
        )

    return target
