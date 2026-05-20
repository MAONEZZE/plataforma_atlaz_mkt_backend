from uuid import UUID

from app.contexts.conteudo.domain.exceptions import AulaNaoEncontrada
from app.contexts.conteudo.domain.repositories import AlunoAulaRepository, AulaRepository


class MarcarConcluida:
    def __init__(self, aula_repo: AulaRepository, aluno_aula_repo: AlunoAulaRepository) -> None:
        self._aula_repo = aula_repo
        self._aluno_aula_repo = aluno_aula_repo

    async def execute(self, aula_id: UUID, usuario_id: UUID) -> None:
        aula = await self._aula_repo.por_id(aula_id)
        if aula is None:
            raise AulaNaoEncontrada(f"Aula {aula_id} não encontrada.")
        await self._aluno_aula_repo.marcar_concluida(usuario_id, aula_id)
