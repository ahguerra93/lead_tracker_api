"""Abstract storage service interface for the WhatsApp domain."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional


class IMediaStorageService(ABC):
    """Uploads a local media file to a remote storage bucket."""

    @abstractmethod
    async def upload(
        self,
        file_path: Path,
        storage_path: str,
        content_type: Optional[str] = None,
    ) -> str:
        """Upload *file_path* to *storage_path* inside the bucket.

        Returns the storage path so callers can persist or log it.
        """
