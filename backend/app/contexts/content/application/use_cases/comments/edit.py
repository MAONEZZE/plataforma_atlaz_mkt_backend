from uuid import UUID

from app.contexts.content.domain.entities import Comment
from app.contexts.content.domain.exceptions import (
    CommentNotFound,
    ComentarioNaoPertenceAoUsuario,
)
from app.contexts.content.domain.repositories import ComentarioRepository
from app.shared.utils import now_sp


class EditComment:
    def __init__(self, repo: CommentRepository) -> None:
        self._repo = repo

    async def execute(
        self, comentario_id: UUID, usuario_id: UUID, is_admin: bool, texto: str
    ) -> Comment:
        comentario = await self._repo.get_by_id(comentario_id)
        if comentario is None:
            raise CommentNotFound(f"Comentário {comentario_id} não encontrado.")

        if not is_admin and comentario.usuario_id != usuario_id:
            raise ComentarioNaoPertenceAoUsuario("Sem permissão para editar este comentário.")

        updated = Comment(
            id=comentario.id,
            aula_id=comentario.aula_id,
            usuario_id=comentario.usuario_id,
            texto=texto,
            criado_em=comentario.criado_em,
            editado_em=now_sp(),
            apagado_em=comentario.apagado_em,
        )
        return await self._repo.update(updated)
