from uuid import UUID

from app.contexts.usuarios.application.dtos import AtualizarMeInput
from app.contexts.usuarios.domain.entities import Usuario
from app.contexts.usuarios.domain.exceptions import UsuarioNaoEncontrado
from app.contexts.usuarios.domain.repositories import UsuarioRepository
from app.contexts.usuarios.domain.value_objects import InstagramUsername, LinkedinUrl, Telefone


class AtualizarMe:
    def __init__(self, repo: UsuarioRepository) -> None:
        self._repo = repo

    async def execute(self, user_id: UUID, inp: AtualizarMeInput) -> Usuario:
        user = await self._repo.por_id(user_id)
        if user is None:
            raise UsuarioNaoEncontrado("Usuário não encontrado.")

        if inp.nome is not None:
            user.nome = inp.nome
        if inp.telefone is not None:
            Telefone(inp.telefone)
            user.telefone = inp.telefone
        if inp.linkedin_url is not None:
            LinkedinUrl(inp.linkedin_url)
            user.linkedin_url = inp.linkedin_url
        if inp.instagram_username is not None:
            InstagramUsername(inp.instagram_username)
            user.instagram_username = inp.instagram_username

        return await self._repo.atualizar(user)
