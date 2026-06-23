"""
Storage provider abstractions for Evidence uploads.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Protocol


class StorageProvider(Protocol):
    """Abstract interface for file storage, allowing future cloud migration."""

    def save_file(self, relative_path: str, contents: bytes) -> str:
        """Save a file and return the full path/URI."""
        ...

    def get_file_path(self, relative_path: str) -> Path:
        """Retrieve the local path to a file, verifying it exists."""
        ...

    def delete_file(self, relative_path: str) -> None:
        """Delete a file if it exists."""
        ...


class LocalStorageProvider:
    """Local filesystem implementation of StorageProvider."""

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir

    def save_file(self, relative_path: str, contents: bytes) -> str:
        """Save bytes to a local file, creating directories as needed."""
        target_path = self.base_dir / relative_path

        # Verify it doesn't escape base_dir (path traversal protection)
        if not str(target_path.resolve()).startswith(str(self.base_dir.resolve())):
            raise ValueError("Path traversal detected")

        target_path.parent.mkdir(parents=True, exist_ok=True)

        with open(target_path, "wb") as f:
            f.write(contents)

        return str(target_path)

    def get_file_path(self, relative_path: str) -> Path:
        """Retrieve a file's Path, raising FileNotFoundError if missing."""
        target_path = self.base_dir / relative_path
        if not str(target_path.resolve()).startswith(str(self.base_dir.resolve())):
            raise ValueError("Path traversal detected")

        if not target_path.exists() or not target_path.is_file():
            raise FileNotFoundError(f"File not found: {relative_path}")

        return target_path

    def delete_file(self, relative_path: str) -> None:
        """Delete a local file securely."""
        target_path = self.base_dir / relative_path
        if not str(target_path.resolve()).startswith(str(self.base_dir.resolve())):
            raise ValueError("Path traversal detected")

        if target_path.exists() and target_path.is_file():
            os.remove(target_path)
