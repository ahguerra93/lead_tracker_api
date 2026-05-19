"""Pydantic schemas for the WhatsApp Cloud API webhook payload.

These models represent the *wire format* sent by Meta — they live in the
presentation layer because they are an external API contract, not a domain
concept. The service layer consumes these typed objects instead of raw dicts.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class WebhookProfile(BaseModel):
    name: Optional[str] = None


class WebhookContact(BaseModel):
    profile: WebhookProfile
    wa_id: str
    # WhatsApp's own opaque string identifier (e.g. "BO.1739782080735949").
    # NOT the same as the internal application user_id stored in the DB.
    user_id: Optional[str] = None


class WebhookTextContent(BaseModel):
    body: str


class WebhookMediaContent(BaseModel):
    """Shared structure for image / document / video / audio / sticker."""

    id: str                          # WhatsApp media object ID
    url: Optional[str] = None        # Downloadable URL (present in webhook events)
    mime_type: Optional[str] = None
    sha256: Optional[str] = None
    caption: Optional[str] = None    # Text caption attached to the media


class WebhookReactionContent(BaseModel):
    """Emoji reaction to a previously sent message."""

    message_id: str   # whatsapp_message_id of the message being reacted to
    emoji: str


class WebhookMessage(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    # "from" is a reserved Python keyword — map it via an alias.
    from_: str = Field(alias="from")
    from_user_id: Optional[str] = None
    timestamp: str                   # Unix epoch as a string in Meta's payload
    type: str

    # Optional typed content fields — only one will be set per message.
    text: Optional[WebhookTextContent] = None
    image: Optional[WebhookMediaContent] = None
    document: Optional[WebhookMediaContent] = None
    video: Optional[WebhookMediaContent] = None
    audio: Optional[WebhookMediaContent] = None
    sticker: Optional[WebhookMediaContent] = None
    reaction: Optional[WebhookReactionContent] = None


class WebhookMetadata(BaseModel):
    display_phone_number: str
    phone_number_id: str


class WebhookValue(BaseModel):
    messaging_product: str
    metadata: WebhookMetadata
    contacts: List[WebhookContact] = []
    messages: List[WebhookMessage] = []


class WebhookChange(BaseModel):
    value: WebhookValue
    field: str


class WebhookEntry(BaseModel):
    id: str
    changes: List[WebhookChange]


class WebhookPayload(BaseModel):
    object: str
    entry: List[WebhookEntry]


class ContextMessage(BaseModel):
    role: str                    # "customer" (incoming) or "agent" (outgoing)
    type: str                    # "text", "image", "document", etc.
    text: Optional[str] = None
    media_url: Optional[str] = None


class LeadExtractionResponse(BaseModel):
    intent: str
    summary: str
    location: Optional[str] = None
    products: List[str] = []
    customer_needs: List[str] = []
    budget_hint: Optional[str] = None
    lead_temperature: str = "cold"


class ConversationResponse(BaseModel):
    id: Optional[int] = None
    contact_id: int
    phone_number_id: str
    created_at: datetime
    updated_at: datetime


class ContactInfo(BaseModel):
    wa_id: str
    name: Optional[str] = None


class MessageSummary(BaseModel):
    id: Optional[int] = None
    direction: str
    message_type: str
    text_content: Optional[str] = None
    message_timestamp: datetime
    media_url: Optional[str] = None
    caption: Optional[str] = None


class ConversationListItemResponse(BaseModel):
    id: Optional[int] = None
    contact_id: int
    phone_number_id: str
    created_at: datetime
    updated_at: datetime
    contact: Optional[ContactInfo] = None
    last_message: Optional[MessageSummary] = None


class ConversationDetailResponse(BaseModel):
    id: Optional[int] = None
    contact_id: int
    phone_number_id: str
    created_at: datetime
    updated_at: datetime
    contact: Optional[ContactInfo] = None
    messages: List[MessageSummary] = []
