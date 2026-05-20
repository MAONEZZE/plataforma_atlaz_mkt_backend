from typing import TYPE_CHECKING, Protocol
from uuid import UUID

from app.contexts.auth.domain.entities import User

if TYPE_CHECKING:
    from app.contexts.auth.application.dtos import TokensDTO


class UserAuthRepository(Protocol):
    async def get_by_id(self, user_id: UUID) -> User | None: ...


class SupabaseAuthGateway(Protocol):
    def sign_in_with_password(self, email: str, password: str) -> "TokensDTO": ...
    def sign_out(self, access_token: str) -> None: ...
