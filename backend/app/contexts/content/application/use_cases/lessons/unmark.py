from uuid import UUID

from app.contexts.conteudo.domain.repositories import AlunoAulaRepository


class DesmarcarConcluida:
    def __init__(self, aluno_aula_repo: AlunoAulaRepository) -> None:
        self._aluno_aula_repo = aluno_aula_repo

    async def execute(self, aula_id: UUID, usuario_id: UUID) -> None:
        await self._aluno_aula_repo.desmarcar(usuario_id, aula_id)
