from collections.abc import Callable
from uuid import UUID

from app.contexts.auth.domain.entities import Usuario
from app.contexts.auth.domain.exceptions import ContaInativa, TokenInvalido
from app.contexts.auth.domain.repositories import UsuarioAuthRepository


class ValidarToken:
    def __init__(
        self,
        repo: UsuarioAuthRepository,
        jwt_decoder: Callable[[str], dict[str, object]],
    ) -> None:
        self._repo = repo
        self._jwt_decoder = jwt_decoder

    async def execute(self, token: str) -> Usuario:
        payload = self._jwt_decoder(token)
        user_id = UUID(str(payload["sub"]))
        user = await self._repo.por_id(user_id)
        if user is None:
            raise TokenInvalido("Usuário não encontrado em public.usuario.")
        if user.inativo:
            raise ContaInativa()
        return user
