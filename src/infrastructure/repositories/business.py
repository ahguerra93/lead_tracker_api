"""SQLAlchemy implementation of IBusinessRepository."""
from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...domain.entities.business import Business as BusinessEntity
from ...domain.repositories.business import IBusinessRepository
from ..models.business_models import Business as BusinessORM


class SQLAlchemyBusinessRepository(IBusinessRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _to_entity(self, orm: BusinessORM) -> BusinessEntity:
        return BusinessEntity(
            id=orm.id,
            name=orm.name,
            phone_number_id=orm.phone_number_id,
            display_phone_number=orm.display_phone_number,
            meta_business_account_id=orm.meta_business_account_id,
            meta_access_token=orm.meta_access_token,
            token_expires_at=orm.token_expires_at,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
        )

    async def get_by_phone_number_id(
        self, phone_number_id: str
    ) -> Optional[BusinessEntity]:
        result = await self._session.execute(
            select(BusinessORM).where(
                BusinessORM.phone_number_id == phone_number_id
            )
        )
        orm = result.scalar_one_or_none()
        return self._to_entity(orm) if orm else None

    async def get_by_id(self, id: uuid.UUID) -> Optional[BusinessEntity]:
        result = await self._session.execute(
            select(BusinessORM).where(BusinessORM.id == id)
        )
        orm = result.scalar_one_or_none()
        return self._to_entity(orm) if orm else None
