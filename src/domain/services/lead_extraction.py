"""Abstract interface for the AI-powered lead extraction service.

Kept in the domain layer so the application layer can depend on this
contract without importing any infrastructure or framework code.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class LeadExtraction:
    """Structured lead information extracted from a conversation transcript."""

    intent: str
    summary: str
    location: Optional[str]
    products: list[str]
    customer_needs: list[str]
    budget_hint: Optional[str]
    lead_temperature: str  # "cold" | "warm" | "hot"


class ILeadExtractionService(ABC):
    """Extracts structured lead information from a plain-text conversation transcript."""

    @abstractmethod
    async def extract(self, transcript: str) -> LeadExtraction:
        """Parse *transcript* and return a :class:`LeadExtraction` with intent and summary."""
