"""SQLAlchemy ORM model for the businesses table."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, Text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID

from .base import Base


class Business(Base):
    __tablename__ = "businesses"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    name = Column(Text, nullable=False)
    phone_number_id = Column(Text, unique=True, nullable=False)
    display_phone_number = Column(Text, nullable=True)
    meta_business_account_id = Column(Text, nullable=True)
    meta_access_token = Column(Text, nullable=True)
    token_expires_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_at = Column(
        TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at = Column(
        TIMESTAMP(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
