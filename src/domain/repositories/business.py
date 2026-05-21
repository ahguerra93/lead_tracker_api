"""Abstract repository interface for the Business domain."""
from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from typing import Optional

from ..entities.business import Business


class IBusinessRepository(ABC):
    @abstractmethod
    async def get_by_phone_number_id(self, phone_number_id: str) -> Optional[Business]:
        pass

    @abstractmethod
    async def get_by_id(self, id: uuid.UUID) -> Optional[Business]:
        pass
