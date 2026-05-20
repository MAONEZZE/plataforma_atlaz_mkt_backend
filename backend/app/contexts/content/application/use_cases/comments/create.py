from uuid import UUID, uuid4

from app.contexts.content.domain.entities import Comment
from app.contexts.content.domain.exceptions import LessonNotFound
from app.contexts.content.domain.repositories import AulaRepository, ComentarioRepository
from app.shared.utils import now_sp


class CreateComment:
    def __init__(self, aula_repo: LessonRepository, comentario_repo: CommentRepository) -> None:
        self._aula_repo = aula_repo
        self._comentario_repo = comentario_repo

    async def execute(self, aula_id: UUID, usuario_id: UUID, texto: str) -> Comment:
        aula = await self._aula_repo.get_by_id(aula_id)
        if aula is None:
            raise LessonNotFound(f"Aula {aula_id} não encontrada.")

        comentario = Comment(
            id=uuid4(),
            aula_id=aula_id,
            usuario_id=usuario_id,
            texto=texto,
            criado_em=now_sp(),
            editado_em=None,
            apagado_em=None,
        )
        return await self._comentario_repo.criar(comentario)
