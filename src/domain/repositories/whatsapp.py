"""Abstract repository interfaces for the WhatsApp domain.

These contracts define what data-access operations exist without coupling
to any specific storage technology. Implementations live in the
infrastructure layer.
"""
from abc import ABC, abstractmethod
from typing import List, Optional

from ..entities.whatsapp import Contact, Conversation, LeadInsight, Media, Message


class IContactRepository(ABC):
    @abstractmethod
    async def get_by_id(self, contact_id: int) -> Optional[Contact]:
        pass

    @abstractmethod
    async def get_by_wa_id(self, wa_id: str) -> Optional[Contact]:
        pass

    @abstractmethod
    async def save(self, contact: Contact) -> Contact:
        pass

    @abstractmethod
    async def list_all(self) -> List[Contact]:
        pass


class IConversationRepository(ABC):
    @abstractmethod
    async def get_by_id(self, conversation_id: int) -> Optional[Conversation]:
        pass

    @abstractmethod
    async def list_recent(self, limit: int = 20) -> List[Conversation]:
        pass

    @abstractmethod
    async def get_by_contact_and_phone(
        self, contact_id: int, phone_number_id: str
    ) -> Optional[Conversation]:
        pass

    @abstractmethod
    async def save(self, conversation: Conversation) -> Conversation:
        pass


class IMessageRepository(ABC):
    @abstractmethod
    async def get_by_whatsapp_id(
        self, whatsapp_message_id: str
    ) -> Optional[Message]:
        pass

    @abstractmethod
    async def save(self, message: Message) -> Message:
        pass

    @abstractmethod
    async def get_recent_messages(
        self, conversation_id: int, limit: int = 10
    ) -> List[Message]:
        pass

    @abstractmethod
    async def get_latest_message_id(self, conversation_id: int) -> Optional[int]:
        """Return the DB id of the most recent message in the conversation,
        or None if the conversation has no messages yet."""
        pass


class IMediaRepository(ABC):
    @abstractmethod
    async def save(self, media: Media) -> Media:
        pass

    @abstractmethod
    async def get_by_message_id(self, message_id: int) -> Optional[Media]:
        pass


class ILeadInsightRepository(ABC):
    @abstractmethod
    async def get_by_conversation_id(
        self, conversation_id: int
    ) -> Optional[LeadInsight]:
        pass

    @abstractmethod
    async def save(self, insight: LeadInsight) -> LeadInsight:
        pass
