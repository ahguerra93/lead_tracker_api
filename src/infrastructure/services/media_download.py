"""Concrete media download service using httpx (async HTTP client).

Keeps all I/O concerns (HTTP, filesystem) out of the domain and application
layers. The domain defines the contract; this module fulfils it.
"""
from __future__ import annotations

import mimetypes
import os
from pathlib import Path
from typing import Optional

import httpx

from ...domain.services.media_download import IMediaDownloadService

# Temporary directory where downloaded files are stored.
MEDIA_DIR = "downloads"

# mimetypes can return non-standard extensions; normalise the common ones.
_MIME_EXT_OVERRIDES: dict[str, str] = {
    ".jpe": ".jpg",
    ".jpeg": ".jpg",
}


class HttpxMediaDownloadService(IMediaDownloadService):
    """Downloads WhatsApp media using an async ``httpx.AsyncClient``."""

    def __init__(self, access_token: str) -> None:
        self._access_token = access_token

    async def download(
        self,
        url: str,
        media_id: str,
        mime_type: Optional[str] = None,
    ) -> Path:
        os.makedirs(MEDIA_DIR, exist_ok=True)

        ext = self._resolve_extension(mime_type)
        file_path = Path(MEDIA_DIR) / f"{media_id}{ext}"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={"Authorization": f"Bearer {self._access_token}"},
                follow_redirects=True,
            )
            response.raise_for_status()

        with open(file_path, "wb") as f:
            f.write(response.content)

        file_size = os.path.getsize(file_path)
        print(f"[MEDIA] Saved media to {file_path}", flush=True)
        print(f"[MEDIA] Saved {file_size} bytes", flush=True)
        return file_path

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_extension(mime_type: Optional[str]) -> str:
        """Return a file extension (with leading dot) for *mime_type*.

        Falls back to an empty string when the type is unknown.
        """
        if not mime_type:
            return ""
        ext = mimetypes.guess_extension(mime_type) or ""
        return _MIME_EXT_OVERRIDES.get(ext, ext)
