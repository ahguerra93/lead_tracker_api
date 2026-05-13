"""Domain entities for the WhatsApp lead tracker.

Pure Pydantic models with no framework or database dependencies.
They represent the core business concepts and encapsulate business rules.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Contact(BaseModel):
    """A WhatsApp contact (lead)."""

    id: Optional[int] = None
    wa_id: str
    user_id: Optional[str] = None
    name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def display_name(self) -> str:
        return self.name or self.wa_id


class Conversation(BaseModel):
    """A conversation thread between the business phone number and a contact."""

    id: Optional[int] = None
    contact_id: int
    phone_number_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Message(BaseModel):
    """A single WhatsApp message within a conversation."""

    id: Optional[int] = None
    whatsapp_message_id: str
    conversation_id: int
    contact_id: int
    direction: str          # "incoming" or "outgoing"
    message_type: str       # "text", "image", "document", etc.
    text_content: Optional[str] = None
    message_timestamp: datetime
    processed: bool = False
    raw_payload: dict[str, Any]
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def is_incoming(self) -> bool:
        return self.direction == "incoming"

    def is_outgoing(self) -> bool:
        return self.direction == "outgoing"

    def mark_as_processed(self) -> None:
        self.processed = True


class Media(BaseModel):
    """A media attachment associated with a message."""

    id: Optional[int] = None
    message_id: int
    media_type: str
    mime_type: Optional[str] = None
    sha256: Optional[str] = None
    meta_media_id: Optional[str] = None
    media_url: str
    storage_path: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


class LeadInsight(BaseModel):
    """AI-extracted lead intelligence cached per conversation."""

    id: Optional[int] = None
    conversation_id: int
    intent: Optional[str] = None
    summary: Optional[str] = None
    location: Optional[str] = None
    products: List[str] = Field(default_factory=list)
    customer_needs: List[str] = Field(default_factory=list)
    budget_hint: Optional[str] = None
    lead_temperature: Optional[str] = None  # "cold" | "warm" | "hot"
    raw_ai_response: Optional[Dict[str, Any]] = None
    last_analyzed_message_id: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
