from typing import Protocol
from uuid import UUID

from app.domain.user_module.user_model import User


class UserRepository(Protocol):
    async def get_by_id(self, user_id: UUID) -> User | None: ...
    async def update(self, user: User) -> User: ...
