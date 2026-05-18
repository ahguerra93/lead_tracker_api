"""Conversation read application service.

Owns read-only conversation retrieval use cases while keeping HTTP concerns
outside the application layer.
"""
from __future__ import annotations

from ...domain.entities.whatsapp import Conversation
from ...domain.unit_of_work import IUnitOfWork


class ConversationService:
    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    async def list_conversations(self, limit: int = 20) -> list[Conversation]:
        async with self._uow as uow:
            return await uow.conversations.list_recent(limit)

    async def get_conversation(self, conversation_id: int) -> Conversation | None:
        async with self._uow as uow:
            return await uow.conversations.get_by_id(conversation_id)