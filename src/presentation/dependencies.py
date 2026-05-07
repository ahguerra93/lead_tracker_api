"""FastAPI dependency providers.

Wires infrastructure implementations to domain interfaces and
injects application services into route handlers.
"""
from typing import Annotated

from fastapi import Depends

from ..infrastructure.db import async_session_factory
from ..infrastructure.unit_of_work import SQLAlchemyUnitOfWork
from ..application.services.whatsapp_service import WhatsAppWebhookService
from ..domain.unit_of_work import IUnitOfWork


def get_unit_of_work() -> IUnitOfWork:
    return SQLAlchemyUnitOfWork(async_session_factory)


def get_whatsapp_service(
    uow: Annotated[IUnitOfWork, Depends(get_unit_of_work)],
) -> WhatsAppWebhookService:
    return WhatsAppWebhookService(uow)


# Convenience type alias for use in route signatures
WhatsAppServiceDep = Annotated[
    WhatsAppWebhookService, Depends(get_whatsapp_service)
]
