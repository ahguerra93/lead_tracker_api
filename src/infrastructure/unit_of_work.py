"""SQLAlchemy implementation of the Unit of Work pattern.

Manages a single AsyncSession for the lifetime of one business
transaction. All repositories share the same session so that a single
commit/rollback covers all changes made in a use case.
"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ..domain.unit_of_work import IUnitOfWork
from .repositories.business import SQLAlchemyBusinessRepository
from .repositories.whatsapp import (
    SQLAlchemyContactRepository,
    SQLAlchemyConversationRepository,
    SQLAlchemyLeadInsightRepository,
    SQLAlchemyMediaRepository,
    SQLAlchemyMessageRepository,
)


class SQLAlchemyUnitOfWork(IUnitOfWork):
    def __init__(self, session_factory: async_sessionmaker) -> None:
        self._session_factory = session_factory

    async def __aenter__(self) -> SQLAlchemyUnitOfWork:
        self._session: AsyncSession = self._session_factory()
        self.businesses = SQLAlchemyBusinessRepository(self._session)
        self.contacts = SQLAlchemyContactRepository(self._session)
        self.conversations = SQLAlchemyConversationRepository(self._session)
        self.messages = SQLAlchemyMessageRepository(self._session)
        self.media = SQLAlchemyMediaRepository(self._session)
        self.lead_insights = SQLAlchemyLeadInsightRepository(self._session)
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.rollback()
        await self._session.close()

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()
