"""Conversation context use-case service.

Retrieves the most recent messages for a conversation and normalises
them into an AI-ready structure that can be fed directly to any LLM
or context-analysis layer.
"""
from __future__ import annotations

from typing import List, Optional

from ...domain.repositories.whatsapp import IMediaRepository, IMessageRepository
from ...domain.unit_of_work import IUnitOfWork
from ...presentation.schemas.whatsapp import ContextMessage

_MEDIA_TYPES = {"image", "document", "video", "audio", "sticker"}


# ---------------------------------------------------------------------------
# Module-level utility — usable inside any open UoW without opening a new one
# ---------------------------------------------------------------------------

async def build_context(
    messages_repo: IMessageRepository,
    media_repo: IMediaRepository,
    conversation_id: int,
    limit: int = 10,
) -> List[ContextMessage]:
    """Fetch and normalise the most recent *limit* messages for a conversation.

    Accepts raw repository references so it can be called from within an
    already-open Unit of Work without starting a nested transaction.
    """
    messages = await messages_repo.get_recent_messages(conversation_id, limit)

    context: List[ContextMessage] = []
    for message in messages:
        media_url: Optional[str] = None

        if message.message_type in _MEDIA_TYPES and message.id is not None:
            media = await media_repo.get_by_message_id(message.id)
            if media is not None:
                media_url = media.storage_path or media.media_url

        context.append(_normalize(message, media_url))

    return context


def _normalize(message, media_url: Optional[str]) -> ContextMessage:
    role = "customer" if message.direction == "incoming" else "agent"

    text = message.text_content
    if text is None and message.message_type in _MEDIA_TYPES:
        payload_content = message.raw_payload.get(message.message_type, {})
        text = payload_content.get("caption") if isinstance(payload_content, dict) else None

    return ContextMessage(
        role=role,
        type=message.message_type,
        text=text,
        media_url=media_url,
    )


_TYPE_LABELS: dict[str, str] = {
    "image": "[Image attached]",
    "document": "[Document attached]",
    "video": "[Video attached]",
    "audio": "[Audio attached]",
    "sticker": "[Sticker attached]",
    "reaction": "[Reaction]",
}


def format_as_transcript(context: List[ContextMessage]) -> str:
    """Render a list of context messages as a human-readable transcript string
    suitable for feeding into an AI extraction pipeline."""
    blocks: List[str] = []
    for msg in context:
        lines = [f"{msg.role.capitalize()}:"]

        if msg.type == "text":
            if msg.text:
                lines.append(msg.text)
        else:
            label = _TYPE_LABELS.get(msg.type, f"[{msg.type.capitalize()} attached]")
            lines.append(label)
            if msg.text:
                lines.append(msg.text)

        blocks.append("\n".join(lines))

    return "\n\n".join(blocks)


# ---------------------------------------------------------------------------
# Standalone service — owns its own UoW for the API endpoint
# ---------------------------------------------------------------------------

class ConversationContextService:
    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    async def get_recent_context(
        self,
        conversation_id: int,
        limit: int = 10,
    ) -> List[ContextMessage]:
        """Return the last *limit* messages of a conversation as normalised
        context entries, sorted chronologically (oldest first)."""
        async with self._uow as uow:
            return await build_context(uow.messages, uow.media, conversation_id, limit)
