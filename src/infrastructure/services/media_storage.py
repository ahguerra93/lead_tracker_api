"""Supabase Storage implementation of IMediaStorageService.

The supabase-py client is synchronous, so uploads are offloaded to a
thread pool via asyncio.to_thread to avoid blocking the event loop.
"""
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

from supabase import create_client, Client

from ...domain.services.media_storage import IMediaStorageService


class SupabaseMediaStorageService(IMediaStorageService):
    def __init__(self, url: str, service_role_key: str, bucket: str) -> None:
        if not url:
            raise ValueError(
                "SUPABASE_URL is not set. Add it to your environment variables."
            )
        if not service_role_key:
            raise ValueError(
                "SUPABASE_SERVICE_ROLE_KEY is not set. Add it to your environment variables."
            )
        self._bucket = bucket
        self._client: Client = create_client(url, service_role_key)

    async def upload(
        self,
        file_path: Path,
        storage_path: str,
        content_type: Optional[str] = None,
    ) -> str:
        file_bytes = file_path.read_bytes()
        file_options = {"content-type": content_type} if content_type else {}

        await asyncio.to_thread(
            self._client.storage.from_(self._bucket).upload,
            path=storage_path,
            file=file_bytes,
            file_options=file_options,
        )

        print(f"[STORAGE] Uploaded to bucket '{self._bucket}' at {storage_path}", flush=True)
        return storage_path
