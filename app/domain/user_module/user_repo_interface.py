from typing import Protocol
from uuid import UUID

from app.domain.user_module.user_model import User


class UserRepository(Protocol):
    async def get_by_id(self, user_id: UUID) -> User | None: ...
    async def update(self, user: User) -> User: ...
    async def upsert_new(self, user: User) -> None: ...
    async def list_clients(
        self,
        page: int,
        page_size: int,
        search: str | None = None,
        sort: str | None = None,
        order: str = "asc",
    ) -> tuple[list[User], int]: ...
    async def assign_product(self, user_id: UUID, product_id: UUID | None) -> None: ...
    async def deactivate(self, user_id: UUID) -> None: ...
