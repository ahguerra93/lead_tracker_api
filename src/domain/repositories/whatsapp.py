"""Abstract repository interfaces for the WhatsApp domain.

These contracts define what data-access operations exist without coupling
to any specific storage technology. Implementations live in the
infrastructure layer.
"""
from abc import ABC, abstractmethod
from typing import List, Optional

from ..entities.whatsapp import Contact, Conversation, Media, Message


class IContactRepository(ABC):
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
    async def list_by_conversation(
        self, conversation_id: int
    ) -> List[Message]:
        pass


class IMediaRepository(ABC):
    @abstractmethod
    async def save(self, media: Media) -> Media:
        pass
