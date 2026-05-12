"""Lead extraction application service.

Fetches the recent conversation transcript from the database and runs
AI-powered lead extraction, returning structured intent and summary data.
Does not persist the result — callers decide what to do with it.
"""
from __future__ import annotations

from ...domain.services.lead_extraction import ILeadExtractionService, LeadExtraction
from ...domain.unit_of_work import IUnitOfWork
from ..services.conversation_context_service import build_context, format_as_transcript


class LeadExtractionService:
    def __init__(
        self,
        uow: IUnitOfWork,
        lead_extractor: ILeadExtractionService,
    ) -> None:
        self._uow = uow
        self._lead_extractor = lead_extractor

    async def extract_from_conversation(
        self,
        conversation_id: int,
        limit: int = 10,
    ) -> LeadExtraction:
        """Fetch the last *limit* messages for *conversation_id*, format them
        as a transcript, and run lead extraction. Returns the result without
        storing anything in the database."""
        async with self._uow as uow:
            context = await build_context(uow.messages, uow.media, conversation_id, limit)

        transcript = format_as_transcript(context)
        print(f"[LEAD_EXTRACTION_SERVICE] Transcript for conversation {conversation_id}:\n{transcript}", flush=True)

        return await self._lead_extractor.extract(transcript)
