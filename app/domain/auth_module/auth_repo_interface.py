from typing import TYPE_CHECKING, Protocol
from uuid import UUID

from app.domain.auth_module.auth_model import User

if TYPE_CHECKING:
    from app.api.controllers.auth_module.auth_dto.auth_dto import TokensDTO


class UserAuthRepository(Protocol):
    async def get_by_id(self, user_id: UUID) -> User | None: ...


class SupabaseAuthGateway(Protocol):
    def sign_in_with_password(self, email: str, password: str) -> "TokensDTO": ...
    def sign_out(self, access_token: str) -> None: ...
