from uuid import UUID

from app.contexts.content.domain.repositories import AlunoAulaRepository


class Unmark:
    def __init__(self, aluno_aula_repo: AlunoAulaRepository) -> None:
        self._aluno_aula_repo = aluno_aula_repo

    async def execute(self, aula_id: UUID, usuario_id: UUID) -> None:
        await self._aluno_aula_repo.unmark(usuario_id, aula_id)
