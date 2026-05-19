"""Conversation read application service.

Owns read-only conversation retrieval use cases while keeping HTTP concerns
outside the application layer.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ...domain.entities.whatsapp import Contact, Conversation, Message
from ...domain.unit_of_work import IUnitOfWork


_MEDIA_TYPES = {"image", "document", "video", "audio", "sticker"}


@dataclass
class ConversationSummary:
    """Conversation with its contact info and most recent message."""
    conversation: Conversation
    contact: Contact | None
    last_message: Message | None


@dataclass
class ConversationDetail:
    """Conversation with its contact info and last N messages (chronological)."""
    conversation: Conversation
    contact: Contact | None
    messages: list["ConversationMessageDetail"] = field(default_factory=list)


@dataclass
class ConversationMessageDetail:
    """Message data enriched with optional media link and caption."""
    message: Message
    media_url: str | None = None
    caption: str | None = None


class ConversationService:
    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    async def list_conversations(self, limit: int = 20) -> list[Conversation]:
        async with self._uow as uow:
            return await uow.conversations.list_recent(limit)

    async def get_conversation(self, conversation_id: int) -> Conversation | None:
        async with self._uow as uow:
            return await uow.conversations.get_by_id(conversation_id)

    async def list_conversations_with_details(
        self, limit: int = 20
    ) -> list[ConversationSummary]:
        async with self._uow as uow:
            conversations = await uow.conversations.list_recent(limit)
            result: list[ConversationSummary] = []
            for conv in conversations:
                contact = await uow.contacts.get_by_id(conv.contact_id)
                msgs = await uow.messages.get_recent_messages(conv.id, 1)
                last_message = msgs[-1] if msgs else None
                result.append(ConversationSummary(conv, contact, last_message))
            return result

    async def get_conversation_with_details(
        self, conversation_id: int
    ) -> ConversationDetail | None:
        async with self._uow as uow:
            conv = await uow.conversations.get_by_id(conversation_id)
            if conv is None:
                return None
            contact = await uow.contacts.get_by_id(conv.contact_id)
            messages = await uow.messages.get_recent_messages(conv.id, 5)

            detailed_messages: list[ConversationMessageDetail] = []
            for message in messages:
                media_url: str | None = None
                caption: str | None = None

                if message.message_type in _MEDIA_TYPES:
                    if message.id is not None:
                        media = await uow.media.get_by_message_id(message.id)
                        if media is not None:
                            media_url = media.storage_path or media.media_url

                    payload_content = message.raw_payload.get(message.message_type, {})
                    if isinstance(payload_content, dict):
                        caption_value = payload_content.get("caption")
                        if isinstance(caption_value, str):
                            caption = caption_value

                detailed_messages.append(
                    ConversationMessageDetail(
                        message=message,
                        media_url=media_url,
                        caption=caption,
                    )
                )

            return ConversationDetail(conv, contact, detailed_messages)