from uuid import UUID

from app.contexts.conteudo.domain.exceptions import (
    ComentarioNaoEncontrado,
    ComentarioNaoPertenceAoUsuario,
)
from app.contexts.conteudo.domain.repositories import ComentarioRepository


class ApagarComentario:
    def __init__(self, repo: ComentarioRepository) -> None:
        self._repo = repo

    async def execute(self, comentario_id: UUID, usuario_id: UUID, is_admin: bool) -> None:
        comentario = await self._repo.por_id(comentario_id)
        if comentario is None:
            raise ComentarioNaoEncontrado(f"Comentário {comentario_id} não encontrado.")

        if not is_admin and comentario.usuario_id != usuario_id:
            raise ComentarioNaoPertenceAoUsuario("Sem permissão para apagar este comentário.")

        await self._repo.apagar(comentario_id)
