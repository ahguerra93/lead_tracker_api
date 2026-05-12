"""OpenAI implementation of the lead extraction service.

Uses gpt-4.1-mini with JSON mode to extract structured lead information
from a WhatsApp conversation transcript.
"""
from __future__ import annotations

import json
import os

from openai import AsyncOpenAI

from ...domain.services.lead_extraction import ILeadExtractionService, LeadExtraction

_SYSTEM_PROMPT = (
    "You extract structured lead information from WhatsApp conversations. "
    "Return ONLY valid JSON."
)

_USER_TEMPLATE = "Conversation:\n\n{transcript}"


class OpenAILeadExtractionService(ILeadExtractionService):
    """Calls the OpenAI Chat Completions API to extract lead intent and summary."""

    def __init__(self, api_key: str | None = None) -> None:
        self._client = AsyncOpenAI(api_key=api_key or os.environ["OPENAI_API_KEY"])

    async def extract(self, transcript: str) -> LeadExtraction:
        response = await self._client.chat.completions.create(
            model="gpt-4.1-mini",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": _USER_TEMPLATE.format(transcript=transcript)},
            ],
        )

        raw = response.choices[0].message.content or "{}"
        data: dict = json.loads(raw)

        print(f"[LEAD_EXTRACTION] Raw response: {raw}", flush=True)

        result = LeadExtraction(
            intent=data.get("intent", ""),
            summary=data.get("summary", ""),
        )

        print(f"[LEAD_EXTRACTION] Extracted: intent={result.intent!r}, summary={result.summary!r}", flush=True)

        return result
