"""Lead extraction application service.

Fetches the recent conversation transcript from the database and runs
AI-powered lead extraction, caching the result in the lead_insights table.
OpenAI is only called when new messages have arrived since the last analysis.
"""
from __future__ import annotations

from datetime import datetime, timezone

from ...domain.entities.whatsapp import LeadInsight
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
        """Return AI-extracted lead data for *conversation_id*.

        Cache-check flow:
        1. Fetch latest message id + cached insight in one DB round-trip.
        2. If the cached insight covers the latest message, return it immediately.
        3. Otherwise run AI extraction and upsert the result.
        """
        # ── Step 1-3: check cache ────────────────────────────────────────────
        async with self._uow as uow:
            latest_id = await uow.messages.get_latest_message_id(conversation_id)
            cached = await uow.lead_insights.get_by_conversation_id(conversation_id)

            # ── Step 4: return cached result if still fresh ──────────────────
            if (
                cached is not None
                and latest_id is not None
                and cached.last_analyzed_message_id == latest_id
            ):
                print(
                    f"[LEAD_EXTRACTION_SERVICE] Cache hit for conversation "
                    f"{conversation_id} (last_message_id={latest_id})",
                    flush=True,
                )
                return _insight_to_extraction(cached)

            # ── Step 5a: fetch messages for transcript ───────────────────────
            context = await build_context(uow.messages, uow.media, conversation_id, limit)
        # UoW closed — DB session released before the OpenAI call

        # ── Step 5b: build transcript + call AI ─────────────────────────────
        transcript = format_as_transcript(context)
        print(
            f"[LEAD_EXTRACTION_SERVICE] Transcript for conversation "
            f"{conversation_id}:\n{transcript}",
            flush=True,
        )
        result = await self._lead_extractor.extract(transcript)

        # ── Step 5c: persist / update insight ───────────────────────────────
        async with self._uow as uow:
            insight_to_save = LeadInsight(
                id=cached.id if cached is not None else None,
                conversation_id=conversation_id,
                intent=result.intent,
                summary=result.summary,
                location=result.location,
                products=result.products,
                customer_needs=result.customer_needs,
                budget_hint=result.budget_hint,
                lead_temperature=result.lead_temperature,
                raw_ai_response={
                    "intent": result.intent,
                    "summary": result.summary,
                    "location": result.location,
                    "products": result.products,
                    "customer_needs": result.customer_needs,
                    "budget_hint": result.budget_hint,
                    "lead_temperature": result.lead_temperature,
                },
                last_analyzed_message_id=latest_id,
                analyzed_at=datetime.now(timezone.utc),
            )
            await uow.lead_insights.save(insight_to_save)
            await uow.commit()

        print(
            f"[LEAD_EXTRACTION_SERVICE] Insight upserted for conversation "
            f"{conversation_id}",
            flush=True,
        )
        return result


def _insight_to_extraction(insight: LeadInsight) -> LeadExtraction:
    """Convert a cached LeadInsight entity back to a LeadExtraction dataclass."""
    return LeadExtraction(
        intent=insight.intent or "",
        summary=insight.summary or "",
        location=insight.location,
        products=insight.products,
        customer_needs=insight.customer_needs,
        budget_hint=insight.budget_hint,
        lead_temperature=insight.lead_temperature or "cold",
    )
