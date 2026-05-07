from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, TIMESTAMP, JSON, UniqueConstraint, Index, Boolean
from sqlalchemy.orm import relationship
from .base import Base


class Contact(Base):
    """WhatsApp contact model."""
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True)
    wa_id = Column(String(255), unique=True, nullable=False)  # e.g., "59167197142"
    user_id = Column(Integer, nullable=True)
    name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    conversations = relationship("Conversation", back_populates="contact", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="contact", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_contacts_wa_id", "wa_id"),
        Index("ix_contacts_user_id", "user_id"),
    )


class Conversation(Base):
    """Conversation between a business and a contact."""
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True)
    contact_id = Column(Integer, ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False)
    phone_number_id = Column(String(255), nullable=False)  # Business phone number ID
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    contact = relationship("Contact", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_conversations_contact_id", "contact_id"),
        Index("ix_conversations_phone_number_id", "phone_number_id"),
    )


class Message(Base):
    """WhatsApp message model."""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)
    whatsapp_message_id = Column(String(255), unique=True, nullable=False)  # e.g., "wamid..."
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    contact_id = Column(Integer, ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False)
    
    direction = Column(String(20), nullable=False)  # "incoming" or "outgoing"
    type = Column(String(50), nullable=False)  # "text", "image", "document", etc.
    
    text_content = Column(Text, nullable=True)
    message_timestamp = Column(TIMESTAMP, nullable=False)  # From webhook
    processed = Column(Boolean, default=False, nullable=False)  # Whether message has been processed
    raw_payload = Column(JSON, nullable=False)  # Full webhook payload
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    contact = relationship("Contact", back_populates="messages")
    media = relationship("Media", back_populates="message", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_messages_whatsapp_message_id", "whatsapp_message_id"),
        Index("ix_messages_conversation_id", "conversation_id"),
        Index("ix_messages_contact_id", "contact_id"),
    )


class Media(Base):
    """Media attachment from a WhatsApp message."""
    __tablename__ = "media"

    id = Column(Integer, primary_key=True)
    message_id = Column(Integer, ForeignKey("messages.id", ondelete="CASCADE"), nullable=False)
    
    media_type = Column(String(50), nullable=False)  # "image", "document", "video", "audio", etc.
    mime_type = Column(String(100), nullable=True)  # e.g., "image/jpeg"
    sha256 = Column(String(64), nullable=True)  # SHA256 hash
    meta_media_id = Column(String(255), nullable=True)  # e.g., "2463061677494161"
    media_url = Column(Text, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    message = relationship("Message", back_populates="media")

    __table_args__ = (
        Index("ix_media_message_id", "message_id"),
        Index("ix_media_meta_media_id", "meta_media_id"),
    )
