"""WhatsApp webhook use-case service.

Orchestrates the flow from a raw webhook payload to persisted domain
objects. Contains no business rules itself — it delegates to domain
entities and coordinates via the Unit of Work.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from ...domain.entities.whatsapp import Contact, Conversation, Media, Message
from ...domain.unit_of_work import IUnitOfWork
from ...presentation.schemas.whatsapp import (
    WebhookContact,
    WebhookMediaContent,
    WebhookMessage,
    WebhookPayload,
    WebhookValue,
)


class WhatsAppWebhookService:
    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    async def process_incoming_webhook(self, payload: WebhookPayload) -> None:
        """Entry point: parse a typed WhatsApp Cloud API webhook payload and
        persist the contacts, conversations, messages, and media it contains."""
        if payload.object != "whatsapp_business_account":
            return

        async with self._uow as uow:
            for entry in payload.entry:
                for change in entry.changes:
                    if change.field == "messages":
                        await self._handle_messages(uow, change.value)
            await uow.commit()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _handle_messages(
        self, uow: IUnitOfWork, value: WebhookValue
    ) -> None:
        phone_number_id: str = value.metadata.phone_number_id

        for msg in value.messages:
            # 1. Get or create contact
            contact = await self._get_or_create_contact(
                uow, msg.from_, value.contacts
            )

            # 2. Get or create conversation
            conversation = await self._get_or_create_conversation(
                uow, contact.id, phone_number_id  # type: ignore[arg-type]
            )

            # 3. Deduplicate: skip if message already stored
            if await uow.messages.get_by_whatsapp_id(msg.id) is not None:
                continue

            # 4. Persist message
            message = await uow.messages.save(
                self._build_message(msg, conversation.id, contact.id)  # type: ignore[arg-type]
            )

            # 5. Persist media attachment if present
            media_content = self._extract_media(msg)
            if media_content and message.id is not None:
                await uow.media.save(
                    Media(
                        message_id=message.id,
                        media_type=msg.type,
                        mime_type=media_content.mime_type,
                        sha256=media_content.sha256,
                        meta_media_id=media_content.id,
                        # Use the downloadable URL; fall back to the media ID
                        # if the URL is absent (e.g. some sticker payloads).
                        media_url=media_content.url or media_content.id,
                    )
                )

    @staticmethod
    async def _get_or_create_contact(
        uow: IUnitOfWork,
        wa_id: str,
        contacts: List[WebhookContact],
    ) -> Contact:
        contact_name: Optional[str] = None
        for c in contacts:
            if c.wa_id == wa_id:
                contact_name = c.profile.name
                break

        contact = await uow.contacts.get_by_wa_id(wa_id)
        if contact is None:
            contact = await uow.contacts.save(
                Contact(wa_id=wa_id, name=contact_name)
            )
        elif contact_name and contact.name != contact_name:
            contact.name = contact_name
            contact = await uow.contacts.save(contact)

        return contact

    @staticmethod
    async def _get_or_create_conversation(
        uow: IUnitOfWork,
        contact_id: int,
        phone_number_id: str,
    ) -> Conversation:
        conversation = await uow.conversations.get_by_contact_and_phone(
            contact_id, phone_number_id
        )
        if conversation is None:
            conversation = await uow.conversations.save(
                Conversation(
                    contact_id=contact_id,
                    phone_number_id=phone_number_id,
                )
            )
        return conversation

    @staticmethod
    def _build_message(
        msg: WebhookMessage,
        conversation_id: int,
        contact_id: int,
    ) -> Message:
        text_content: Optional[str] = msg.text.body if msg.text else None
        msg_timestamp = datetime.fromtimestamp(int(msg.timestamp), tz=timezone.utc)

        return Message(
            whatsapp_message_id=msg.id,
            conversation_id=conversation_id,
            contact_id=contact_id,
            direction="incoming",
            message_type=msg.type,
            text_content=text_content,
            message_timestamp=msg_timestamp,
            raw_payload=msg.model_dump(by_alias=True),
        )

    @staticmethod
    def _extract_media(msg: WebhookMessage) -> Optional[WebhookMediaContent]:
        return (
            msg.image
            or msg.document
            or msg.video
            or msg.audio
            or msg.sticker
        )
