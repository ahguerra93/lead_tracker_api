"""WhatsApp webhook use-case service.

Orchestrates the flow from a raw webhook payload to persisted domain
objects. Contains no business rules itself — it delegates to domain
entities and coordinates via the Unit of Work.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from ...domain.entities.whatsapp import Contact, Conversation, Media, Message
from ...domain.services.media_download import IMediaDownloadService
from ...domain.services.media_storage import IMediaStorageService
from ...domain.unit_of_work import IUnitOfWork
from ...presentation.schemas.whatsapp import (
    WebhookContact,
    WebhookMediaContent,
    WebhookMessage,
    WebhookPayload,
    WebhookValue,
)
from .conversation_context_service import build_context, format_as_transcript


class WhatsAppWebhookService:
    def __init__(
        self,
        uow: IUnitOfWork,
        media_downloader: IMediaDownloadService,
        media_storage: IMediaStorageService,
    ) -> None:
        self._uow = uow
        self._media_downloader = media_downloader
        self._media_storage = media_storage

    async def process_incoming_webhook(self, payload: WebhookPayload) -> None:
        """Entry point: parse a typed WhatsApp Cloud API webhook payload and
        persist the contacts, conversations, messages, and media it contains."""
        print(f"[SERVICE] process_incoming_webhook called with object: {payload.object}", flush=True)
        if payload.object != "whatsapp_business_account":
            print(f"[SERVICE] Ignoring non-whatsapp_business_account object", flush=True)
            return

        print(f"[SERVICE] Processing {len(payload.entry)} entries", flush=True)
        async with self._uow as uow:
            for entry in payload.entry:
                for change in entry.changes:
                    if change.field == "messages":
                        print(f"[SERVICE] Processing messages change", flush=True)
                        await self._handle_messages(uow, change.value)
            await uow.commit()
        print(f"[SERVICE] Successfully committed all changes", flush=True)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _handle_messages(
        self, uow: IUnitOfWork, value: WebhookValue
    ) -> None:
        phone_number_id: str = value.metadata.phone_number_id
        print(f"[SERVICE] Handling {len(value.messages)} messages", flush=True)

        business = await uow.businesses.get_by_phone_number_id(phone_number_id)
        if business is None:
            print(
                f"[SERVICE] No business found for phone_number_id={phone_number_id}, skipping",
                flush=True,
            )
            return
        print(
            f"[SERVICE] Resolved business id={business.id} name={business.name}",
            flush=True,
        )

        for msg in value.messages:
            print(f"[SERVICE] Processing message id={msg.id}, type={msg.type}", flush=True)
            # 1. Get or create contact
            contact = await self._get_or_create_contact(
                uow, msg.from_, value.contacts
            )
            print(f"[SERVICE] Got/created contact: {contact.model_dump()}", flush=True)

            # 2. Get or create conversation
            conversation = await self._get_or_create_conversation(
                uow, contact.id, phone_number_id  # type: ignore[arg-type]
            )
            print(f"[SERVICE] Got/created conversation: {conversation.model_dump()}", flush=True)

            # 3. Deduplicate: skip if message already stored
            if await uow.messages.get_by_whatsapp_id(msg.id) is not None:
                print(f"[SERVICE] Message {msg.id} already exists, skipping", flush=True)
                continue

            # 4. Persist message
            built_message = self._build_message(msg, conversation.id, contact.id)  # type: ignore[arg-type]
            print(f"[SERVICE] Built message: {built_message.model_dump()}", flush=True)
            message = await uow.messages.save(built_message)
            print(f"[SERVICE] Saved message with id={message.id}", flush=True)

            # 5. Persist media attachment if present
            media_content = self._extract_media(msg)
            if media_content and message.id is not None:
                media = Media(
                    message_id=message.id,
                    media_type=msg.type,
                    mime_type=media_content.mime_type,
                    sha256=media_content.sha256,
                    meta_media_id=media_content.id,
                    # Use the downloadable URL; fall back to the media ID
                    # if the URL is absent (e.g. some sticker payloads).
                    media_url=media_content.url or media_content.id,
                )
                print(f"[SERVICE] Built media: {media.model_dump()}", flush=True)
                saved_media = await uow.media.save(media)
                print(f"[SERVICE] Saved media with id={saved_media.id}", flush=True)

                # Download the file to a temporary location, then upload to storage
                if media_content.url:
                    if not business.meta_access_token:
                        print(
                            f"[SERVICE] Business has no meta_access_token, skipping download",
                            flush=True,
                        )
                    else:
                        file_path = await self._media_downloader.download(
                            url=media_content.url,
                            media_id=media_content.id,
                            access_token=business.meta_access_token,
                            mime_type=media_content.mime_type,
                        )
                        print(f"[SERVICE] Media file ready at {file_path}", flush=True)

                        storage_path = f"{msg.type}s/{media_content.id}{file_path.suffix}"
                        await self._media_storage.upload(
                            file_path=file_path,
                            storage_path=storage_path,
                            content_type=media_content.mime_type,
                        )
                        print(f"[SERVICE] Uploaded media to storage at {storage_path}", flush=True)

                        saved_media.storage_path = storage_path
                        saved_media = await uow.media.save(saved_media)
                        print(f"[SERVICE] Updated media record with storage_path={storage_path}", flush=True)
            else:
                print(f"[SERVICE] No media to persist for message {msg.id}", flush=True)

            # 6. Build and print conversation context (includes the message just saved)
            if conversation.id is not None:
                context = await build_context(
                    uow.messages, uow.media, conversation.id
                )
                transcript = format_as_transcript(context)
                print(f"[CONTEXT] conversation_id={conversation.id}:\n{transcript}", flush=True)

    @staticmethod
    async def _get_or_create_contact(
        uow: IUnitOfWork,
        wa_id: str,
        contacts: List[WebhookContact],
    ) -> Contact:
        contact_name: Optional[str] = None
        contact_user_id: Optional[str] = None
        for c in contacts:
            if c.wa_id == wa_id:
                contact_name = c.profile.name
                contact_user_id = c.user_id
                print(f"[SERVICE] Found contact in webhook: name={contact_name}, user_id={contact_user_id}, wa_id={wa_id}", flush=True)
                break

        contact = await uow.contacts.get_by_wa_id(wa_id)
        if contact is None:
            contact = await uow.contacts.save(
                Contact(wa_id=wa_id, user_id=contact_user_id, name=contact_name)
            )
            print(f"[SERVICE] Created new contact: {contact.model_dump()}", flush=True)
        elif contact_name and contact.name != contact_name:
            contact.name = contact_name
            contact.user_id = contact_user_id
            contact = await uow.contacts.save(contact)
            print(f"[SERVICE] Updated contact: {contact.model_dump()}", flush=True)
        else:
            print(f"[SERVICE] Contact already exists: {contact.model_dump()}", flush=True)

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
            print(f"[SERVICE] Created new conversation: {conversation.model_dump()}", flush=True)
        else:
            print(f"[SERVICE] Conversation already exists: {conversation.model_dump()}", flush=True)
        return conversation

    @staticmethod
    def _build_message(
        msg: WebhookMessage,
        conversation_id: int,
        contact_id: int,
    ) -> Message:
        # Get text content from text field
        text_content: Optional[str] = msg.text.body if msg.text else None
        
        # Also check for caption in media if no text
        if not text_content:
            media = (
                msg.image
                or msg.document
                or msg.video
                or msg.audio
                or msg.sticker
            )
            if media and media.caption:
                text_content = media.caption
                print(f"[SERVICE] Extracted caption from media: {text_content}", flush=True)

        # Reaction: store the emoji as text_content
        if not text_content and msg.reaction:
            text_content = msg.reaction.emoji
            print(f"[SERVICE] Extracted reaction emoji: {text_content}", flush=True)
        
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
