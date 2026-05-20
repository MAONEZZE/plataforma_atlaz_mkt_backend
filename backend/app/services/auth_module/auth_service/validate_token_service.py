from collections.abc import Callable
from uuid import UUID

from app.domain.auth_module.auth_exceptions import InactiveAccount, InvalidToken
from app.domain.auth_module.auth_model import User
from app.domain.auth_module.auth_repo_interface import UserAuthRepository


class ValidateToken:
    def __init__(
        self,
        repo: UserAuthRepository,
        jwt_decoder: Callable[[str], dict[str, object]],
    ) -> None:
        self._repo = repo
        self._jwt_decoder = jwt_decoder

    async def execute(self, token: str) -> User:
        payload = self._jwt_decoder(token)
        user_id = UUID(str(payload["sub"]))
        user = await self._repo.get_by_id(user_id)
        if user is None:
            raise InvalidToken("Usuário não encontrado em public.usuario.")
        if user.inactive:
            raise InactiveAccount()
        return user
