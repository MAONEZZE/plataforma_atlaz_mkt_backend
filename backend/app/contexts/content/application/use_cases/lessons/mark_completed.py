from uuid import UUID

from app.contexts.content.domain.exceptions import LessonNotFound
from app.contexts.content.domain.repositories import AlunoAulaRepository, AulaRepository


class MarkCompleted:
    def __init__(self, aula_repo: LessonRepository, aluno_aula_repo: AlunoAulaRepository) -> None:
        self._aula_repo = aula_repo
        self._aluno_aula_repo = aluno_aula_repo

    async def execute(self, aula_id: UUID, usuario_id: UUID) -> None:
        aula = await self._aula_repo.get_by_id(aula_id)
        if aula is None:
            raise LessonNotFound(f"Aula {aula_id} não encontrada.")
        await self._aluno_aula_repo.mark_completed(usuario_id, aula_id)
