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
    '''
You extract structured lead information from WhatsApp conversations.

Return ONLY valid JSON.

Use exactly this structure:

{
  "intent": string,
  "summary": string,
  "location": string | null,
  "products": string[],
  "customer_needs": string[],
  "budget_hint": string | null,
  "lead_temperature": "cold" | "warm" | "hot"
}

Rules:
- Do not invent information.
- If data is missing, use null.
- Keep summaries concise.
- Products should be short labels.
- customer_needs should contain practical requirements mentioned by the customer.
- lead_temperature rules:
  - hot: customer shows strong purchase intent, urgency, or asks for quote/pricing
  - warm: customer is interested but missing commitment or details
  - cold: vague curiosity or low intent
'''
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
            location=data.get("location"),
            products=data.get("products") or [],
            customer_needs=data.get("customer_needs") or [],
            budget_hint=data.get("budget_hint"),
            lead_temperature=data.get("lead_temperature", "cold"),
        )

        print(f"[LEAD_EXTRACTION] Extracted: {result}", flush=True)

        return result
