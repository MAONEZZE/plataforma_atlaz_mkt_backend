from uuid import UUID

from app.contexts.usuarios.domain.entities import Usuario
from app.contexts.usuarios.domain.exceptions import UsuarioNaoEncontrado
from app.contexts.usuarios.domain.repositories import UsuarioRepository


class ObterMe:
    def __init__(self, repo: UsuarioRepository) -> None:
        self._repo = repo

    async def execute(self, user_id: UUID) -> Usuario:
        user = await self._repo.por_id(user_id)
        if user is None:
            raise UsuarioNaoEncontrado("Usuário não encontrado.")
        return user
