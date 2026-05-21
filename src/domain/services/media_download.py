"""Abstract service interfaces for the WhatsApp domain.

Kept in the domain layer so the application layer can depend on these
contracts without importing any infrastructure or framework code.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional


class IMediaDownloadService(ABC):
    """Downloads a WhatsApp media file and persists it to a temporary location."""

    @abstractmethod
    async def download(
        self,
        url: str,
        media_id: str,
        access_token: str,
        mime_type: Optional[str] = None,
    ) -> Path:
        """Fetch *url* authenticated with *access_token* and write the
        response body to disk.

        Returns the ``Path`` of the saved file so callers can validate or
        forward it to a storage backend later.
        """
