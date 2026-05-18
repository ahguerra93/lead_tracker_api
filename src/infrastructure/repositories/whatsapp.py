"""SQLAlchemy implementations of the domain repository interfaces.

Each class maps between domain entities and ORM models, keeping the
domain layer free of any SQLAlchemy knowledge.
"""
from typing import List, Optional

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...domain.entities.whatsapp import (
    Contact as ContactEntity,
    Conversation as ConversationEntity,
    LeadInsight as LeadInsightEntity,
    Media as MediaEntity,
    Message as MessageEntity,
)
from ...domain.repositories.whatsapp import (
    IContactRepository,
    IConversationRepository,
    ILeadInsightRepository,
    IMediaRepository,
    IMessageRepository,
)
from ..models.whatsapp_models import (
    Contact as ContactORM,
    Conversation as ConversationORM,
    LeadInsight as LeadInsightORM,
    Media as MediaORM,
    Message as MessageORM,
)


# ---------------------------------------------------------------------------
# Contact
# ---------------------------------------------------------------------------


class SQLAlchemyContactRepository(IContactRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _to_entity(self, orm: ContactORM) -> ContactEntity:
        return ContactEntity(
            id=orm.id,
            wa_id=orm.wa_id,
            user_id=orm.user_id,
            name=orm.name,
            created_at=orm.created_at,
        )

    async def get_by_wa_id(self, wa_id: str) -> Optional[ContactEntity]:
        result = await self._session.execute(
            select(ContactORM).where(ContactORM.wa_id == wa_id)
        )
        orm = result.scalar_one_or_none()
        return self._to_entity(orm) if orm else None

    async def save(self, contact: ContactEntity) -> ContactEntity:
        if contact.id is not None:
            result = await self._session.execute(
                select(ContactORM).where(ContactORM.id == contact.id)
            )
            orm = result.scalar_one_or_none()
            if orm:
                orm.wa_id = contact.wa_id
                orm.user_id = contact.user_id
                orm.name = contact.name
            else:
                orm = ContactORM(
                    wa_id=contact.wa_id,
                    user_id=contact.user_id,
                    name=contact.name,
                )
                self._session.add(orm)
        else:
            orm = ContactORM(
                wa_id=contact.wa_id,
                user_id=contact.user_id,
                name=contact.name,
            )
            self._session.add(orm)

        await self._session.flush()
        return self._to_entity(orm)

    async def list_all(self) -> List[ContactEntity]:
        result = await self._session.execute(select(ContactORM))
        return [self._to_entity(orm) for orm in result.scalars().all()]


# ---------------------------------------------------------------------------
# Conversation
# ---------------------------------------------------------------------------


class SQLAlchemyConversationRepository(IConversationRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _to_entity(self, orm: ConversationORM) -> ConversationEntity:
        return ConversationEntity(
            id=orm.id,
            contact_id=orm.contact_id,
            phone_number_id=orm.phone_number_id,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
        )

    async def get_by_id(self, conversation_id: int) -> Optional[ConversationEntity]:
        result = await self._session.execute(
            select(ConversationORM).where(ConversationORM.id == conversation_id)
        )
        orm = result.scalar_one_or_none()
        return self._to_entity(orm) if orm else None

    async def list_recent(self, limit: int = 20) -> List[ConversationEntity]:
        result = await self._session.execute(
            select(ConversationORM)
            .order_by(desc(ConversationORM.updated_at), desc(ConversationORM.id))
            .limit(limit)
        )
        return [self._to_entity(orm) for orm in result.scalars().all()]

    async def get_by_contact_and_phone(
        self, contact_id: int, phone_number_id: str
    ) -> Optional[ConversationEntity]:
        result = await self._session.execute(
            select(ConversationORM).where(
                ConversationORM.contact_id == contact_id,
                ConversationORM.phone_number_id == phone_number_id,
            )
        )
        orm = result.scalar_one_or_none()
        return self._to_entity(orm) if orm else None

    async def save(self, conversation: ConversationEntity) -> ConversationEntity:
        if conversation.id is not None:
            result = await self._session.execute(
                select(ConversationORM).where(ConversationORM.id == conversation.id)
            )
            orm = result.scalar_one_or_none()
            if orm:
                orm.contact_id = conversation.contact_id
                orm.phone_number_id = conversation.phone_number_id
                orm.updated_at = conversation.updated_at
            else:
                orm = ConversationORM(
                    contact_id=conversation.contact_id,
                    phone_number_id=conversation.phone_number_id,
                )
                self._session.add(orm)
        else:
            orm = ConversationORM(
                contact_id=conversation.contact_id,
                phone_number_id=conversation.phone_number_id,
            )
            self._session.add(orm)

        await self._session.flush()
        return self._to_entity(orm)


# ---------------------------------------------------------------------------
# Message
# ---------------------------------------------------------------------------


class SQLAlchemyMessageRepository(IMessageRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _to_entity(self, orm: MessageORM) -> MessageEntity:
        return MessageEntity(
            id=orm.id,
            whatsapp_message_id=orm.whatsapp_message_id,
            conversation_id=orm.conversation_id,
            contact_id=orm.contact_id,
            direction=orm.direction,
            message_type=orm.type,
            text_content=orm.text_content,
            message_timestamp=orm.message_timestamp,
            processed=orm.processed,
            raw_payload=orm.raw_payload,
            created_at=orm.created_at,
        )

    def _to_orm(self, message: MessageEntity) -> MessageORM:
        return MessageORM(
            whatsapp_message_id=message.whatsapp_message_id,
            conversation_id=message.conversation_id,
            contact_id=message.contact_id,
            direction=message.direction,
            type=message.message_type,
            text_content=message.text_content,
            message_timestamp=message.message_timestamp,
            processed=message.processed,
            raw_payload=message.raw_payload,
        )

    async def get_by_whatsapp_id(
        self, whatsapp_message_id: str
    ) -> Optional[MessageEntity]:
        result = await self._session.execute(
            select(MessageORM).where(
                MessageORM.whatsapp_message_id == whatsapp_message_id
            )
        )
        orm = result.scalar_one_or_none()
        return self._to_entity(orm) if orm else None

    async def save(self, message: MessageEntity) -> MessageEntity:
        if message.id is not None:
            result = await self._session.execute(
                select(MessageORM).where(MessageORM.id == message.id)
            )
            orm = result.scalar_one_or_none()
            if orm:
                orm.processed = message.processed
                orm.text_content = message.text_content
            else:
                orm = self._to_orm(message)
                self._session.add(orm)
        else:
            orm = self._to_orm(message)
            self._session.add(orm)

        await self._session.flush()
        return self._to_entity(orm)

    async def get_recent_messages(
        self, conversation_id: int, limit: int = 10
    ) -> List[MessageEntity]:
        result = await self._session.execute(
            select(MessageORM)
            .where(MessageORM.conversation_id == conversation_id)
            .order_by(desc(MessageORM.message_timestamp))
            .limit(limit)
        )
        rows = result.scalars().all()
        # Reverse to return in chronological (oldest-first) order
        return [self._to_entity(orm) for orm in reversed(rows)]

    async def get_latest_message_id(self, conversation_id: int) -> Optional[int]:
        result = await self._session.execute(
            select(MessageORM.id)
            .where(MessageORM.conversation_id == conversation_id)
            .order_by(desc(MessageORM.message_timestamp))
            .limit(1)
        )
        return result.scalar_one_or_none()


# ---------------------------------------------------------------------------
# Media
# ---------------------------------------------------------------------------


class SQLAlchemyMediaRepository(IMediaRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _to_entity(self, orm: MediaORM) -> MediaEntity:
        return MediaEntity(
            id=orm.id,
            message_id=orm.message_id,
            media_type=orm.media_type,
            mime_type=orm.mime_type,
            sha256=orm.sha256,
            meta_media_id=orm.meta_media_id,
            media_url=orm.media_url,
            storage_path=orm.bucket_url,
            created_at=orm.created_at,
        )

    async def get_by_message_id(self, message_id: int) -> Optional[MediaEntity]:
        result = await self._session.execute(
            select(MediaORM).where(MediaORM.message_id == message_id)
        )
        orm = result.scalars().first()
        return self._to_entity(orm) if orm else None

    async def save(self, media: MediaEntity) -> MediaEntity:
        if media.id is not None:
            result = await self._session.execute(
                select(MediaORM).where(MediaORM.id == media.id)
            )
            orm = result.scalar_one_or_none()
            if orm:
                orm.bucket_url = media.storage_path
            else:
                orm = MediaORM(
                    message_id=media.message_id,
                    media_type=media.media_type,
                    mime_type=media.mime_type,
                    sha256=media.sha256,
                    meta_media_id=media.meta_media_id,
                    media_url=media.media_url,
                    bucket_url=media.storage_path,
                )
                self._session.add(orm)
        else:
            orm = MediaORM(
                message_id=media.message_id,
                media_type=media.media_type,
                mime_type=media.mime_type,
                sha256=media.sha256,
                meta_media_id=media.meta_media_id,
                media_url=media.media_url,
                bucket_url=media.storage_path,
            )
            self._session.add(orm)

        await self._session.flush()
        return self._to_entity(orm)


# ---------------------------------------------------------------------------
# LeadInsight
# ---------------------------------------------------------------------------


class SQLAlchemyLeadInsightRepository(ILeadInsightRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _to_entity(self, orm: LeadInsightORM) -> LeadInsightEntity:
        return LeadInsightEntity(
            id=orm.id,
            conversation_id=orm.conversation_id,
            intent=orm.intent,
            summary=orm.summary,
            location=orm.location,
            products=orm.products or [],
            customer_needs=orm.customer_needs or [],
            budget_hint=orm.budget_hint,
            lead_temperature=orm.lead_temperature,
            raw_ai_response=orm.raw_ai_response,
            last_analyzed_message_id=orm.last_analyzed_message_id,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
            analyzed_at=orm.analyzed_at,
        )

    async def get_by_conversation_id(
        self, conversation_id: int
    ) -> Optional[LeadInsightEntity]:
        result = await self._session.execute(
            select(LeadInsightORM).where(
                LeadInsightORM.conversation_id == conversation_id
            )
        )
        orm = result.scalar_one_or_none()
        return self._to_entity(orm) if orm else None

    async def save(self, insight: LeadInsightEntity) -> LeadInsightEntity:
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)

        if insight.id is not None:
            result = await self._session.execute(
                select(LeadInsightORM).where(LeadInsightORM.id == insight.id)
            )
            orm = result.scalar_one_or_none()
            if orm:
                orm.intent = insight.intent
                orm.summary = insight.summary
                orm.location = insight.location
                orm.products = insight.products
                orm.customer_needs = insight.customer_needs
                orm.budget_hint = insight.budget_hint
                orm.lead_temperature = insight.lead_temperature
                orm.raw_ai_response = insight.raw_ai_response
                orm.last_analyzed_message_id = insight.last_analyzed_message_id
                orm.updated_at = now
                orm.analyzed_at = now
            else:
                orm = LeadInsightORM(
                    conversation_id=insight.conversation_id,
                    intent=insight.intent,
                    summary=insight.summary,
                    location=insight.location,
                    products=insight.products,
                    customer_needs=insight.customer_needs,
                    budget_hint=insight.budget_hint,
                    lead_temperature=insight.lead_temperature,
                    raw_ai_response=insight.raw_ai_response,
                    last_analyzed_message_id=insight.last_analyzed_message_id,
                    analyzed_at=now,
                )
                self._session.add(orm)
        else:
            orm = LeadInsightORM(
                conversation_id=insight.conversation_id,
                intent=insight.intent,
                summary=insight.summary,
                location=insight.location,
                products=insight.products,
                customer_needs=insight.customer_needs,
                budget_hint=insight.budget_hint,
                lead_temperature=insight.lead_temperature,
                raw_ai_response=insight.raw_ai_response,
                last_analyzed_message_id=insight.last_analyzed_message_id,
                analyzed_at=now,
            )
            self._session.add(orm)

        await self._session.flush()
        return self._to_entity(orm)
