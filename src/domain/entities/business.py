"""Business domain entity."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Business(BaseModel):
    """A registered WhatsApp Business account."""

    id: Optional[uuid.UUID] = None
    name: str
    phone_number_id: str
    display_phone_number: Optional[str] = None
    meta_business_account_id: Optional[str] = None
    meta_access_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
