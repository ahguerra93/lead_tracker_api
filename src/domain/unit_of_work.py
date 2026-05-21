"""Abstract Unit of Work interface.

Coordinates all repositories within a single database transaction,
ensuring atomicity across multiple repository operations.
"""
from abc import ABC, abstractmethod
from typing import Self

from .repositories.business import IBusinessRepository
from .repositories.whatsapp import (
    IContactRepository,
    IConversationRepository,
    ILeadInsightRepository,
    IMediaRepository,
    IMessageRepository,
)


class IUnitOfWork(ABC):
    businesses: IBusinessRepository
    contacts: IContactRepository
    conversations: IConversationRepository
    messages: IMessageRepository
    media: IMediaRepository
    lead_insights: ILeadInsightRepository

    @abstractmethod
    async def __aenter__(self) -> Self:
        pass

    @abstractmethod
    async def __aexit__(self, *args: object) -> None:
        pass

    @abstractmethod
    async def commit(self) -> None:
        pass

    @abstractmethod
    async def rollback(self) -> None:
        pass
