"""FastAPI dependency providers.

Wires infrastructure implementations to domain interfaces and
injects application services into route handlers.
"""
from typing import Annotated

from fastapi import Depends

from ..infrastructure.db import async_session_factory
from ..infrastructure.unit_of_work import SQLAlchemyUnitOfWork
from ..infrastructure.services.media_download import HttpxMediaDownloadService
from ..infrastructure.services.media_storage import SupabaseMediaStorageService
from ..infrastructure.services.lead_extraction import OpenAILeadExtractionService
from ..application.services.whatsapp_service import WhatsAppWebhookService
from ..application.services.conversation_context_service import ConversationContextService
from ..application.services.lead_extraction_service import LeadExtractionService
from ..domain.unit_of_work import IUnitOfWork
from ..domain.services.media_download import IMediaDownloadService
from ..domain.services.media_storage import IMediaStorageService
from ..domain.services.lead_extraction import ILeadExtractionService
from config import WhatsAppConfig, SupabaseConfig


def get_unit_of_work() -> IUnitOfWork:
    return SQLAlchemyUnitOfWork(async_session_factory)


def get_media_download_service() -> IMediaDownloadService:
    return HttpxMediaDownloadService(WhatsAppConfig.META_ACCESS_TOKEN)


def get_media_storage_service() -> IMediaStorageService:
    return SupabaseMediaStorageService(
        url=SupabaseConfig.SUPABASE_URL,
        service_role_key=SupabaseConfig.SUPABASE_SERVICE_ROLE_KEY,
        bucket=SupabaseConfig.MEDIA_BUCKET,
    )


def get_whatsapp_service(
    uow: Annotated[IUnitOfWork, Depends(get_unit_of_work)],
    media_downloader: Annotated[IMediaDownloadService, Depends(get_media_download_service)],
    media_storage: Annotated[IMediaStorageService, Depends(get_media_storage_service)],
) -> WhatsAppWebhookService:
    return WhatsAppWebhookService(uow, media_downloader, media_storage)


def get_conversation_context_service(
    uow: Annotated[IUnitOfWork, Depends(get_unit_of_work)],
) -> ConversationContextService:
    return ConversationContextService(uow)


def get_lead_extraction_service_domain() -> ILeadExtractionService:
    return OpenAILeadExtractionService()


def get_lead_extraction_service(
    uow: Annotated[IUnitOfWork, Depends(get_unit_of_work)],
    lead_extractor: Annotated[ILeadExtractionService, Depends(get_lead_extraction_service_domain)],
) -> LeadExtractionService:
    return LeadExtractionService(uow, lead_extractor)


# Convenience type aliases for use in route signatures
WhatsAppServiceDep = Annotated[
    WhatsAppWebhookService, Depends(get_whatsapp_service)
]

ConversationContextServiceDep = Annotated[
    ConversationContextService, Depends(get_conversation_context_service)
]

LeadExtractionServiceDep = Annotated[
    LeadExtractionService, Depends(get_lead_extraction_service)
]
