"""Application service for business lookups."""
from __future__ import annotations

import uuid
from typing import Optional

from ...domain.entities.business import Business
from ...domain.unit_of_work import IUnitOfWork


class BusinessService:
    """Provides read access to Business records for use across the application."""

    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    async def get_by_phone_number_id(
        self, phone_number_id: str
    ) -> Optional[Business]:
        async with self._uow as uow:
            return await uow.businesses.get_by_phone_number_id(phone_number_id)

    async def get_by_id(self, id: uuid.UUID) -> Optional[Business]:
        async with self._uow as uow:
            return await uow.businesses.get_by_id(id)
