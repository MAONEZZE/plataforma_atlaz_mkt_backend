from uuid import UUID

from app.contexts.content.domain.exceptions import (
    CommentNotFound,
    ComentarioNaoPertenceAoUsuario,
)
from app.contexts.content.domain.repositories import ComentarioRepository


class DeleteComment:
    def __init__(self, repo: CommentRepository) -> None:
        self._repo = repo

    async def execute(self, comentario_id: UUID, usuario_id: UUID, is_admin: bool) -> None:
        comentario = await self._repo.get_by_id(comentario_id)
        if comentario is None:
            raise CommentNotFound(f"Comentário {comentario_id} não encontrado.")

        if not is_admin and comentario.usuario_id != usuario_id:
            raise ComentarioNaoPertenceAoUsuario("Sem permissão para apagar este comentário.")

        await self._repo.delete_comment(comentario_id)
