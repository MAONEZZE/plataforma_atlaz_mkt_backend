from uuid import UUID

from app.contexts.conteudo.application.dtos import AulaDetalheDTO, AulaResumoDTO, TrilhaResumoDTO
from app.contexts.conteudo.domain.exceptions import (
    AulaNaoEncontrada,
    ModuloNaoEncontrado,
    TrilhaNaoEncontrada,
)
from app.contexts.conteudo.domain.repositories import (
    AlunoAulaRepository,
    AulaRepository,
    ModuloRepository,
    TrilhaRepository,
)


class ObterAula:
    def __init__(
        self,
        aula_repo: AulaRepository,
        modulo_repo: ModuloRepository,
        trilha_repo: TrilhaRepository,
        aluno_aula_repo: AlunoAulaRepository,
    ) -> None:
        self._aula_repo = aula_repo
        self._modulo_repo = modulo_repo
        self._trilha_repo = trilha_repo
        self._aluno_aula_repo = aluno_aula_repo

    async def execute(self, aula_id: UUID, usuario_id: UUID) -> AulaDetalheDTO:
        aula = await self._aula_repo.por_id(aula_id)
        if aula is None:
            raise AulaNaoEncontrada(f"Aula {aula_id} não encontrada.")

        modulo = await self._modulo_repo.por_id(aula.modulo_id)
        if modulo is None:
            raise ModuloNaoEncontrado(f"Módulo {aula.modulo_id} não encontrado.")

        trilha = await self._trilha_repo.por_id(modulo.trilha_id)
        if trilha is None:
            raise TrilhaNaoEncontrada(f"Trilha {modulo.trilha_id} não encontrada.")

        concluidas = await self._aluno_aula_repo.concluidas_ids(usuario_id)
        proxima = await self._aula_repo.proxima(aula)

        return AulaDetalheDTO(
            id=aula.id,
            modulo_id=aula.modulo_id,
            titulo=aula.titulo,
            descricao=aula.descricao,
            drive_file_id=aula.drive_file_id,
            duracao_minutos=aula.duracao_minutos,
            concluida=aula.id in concluidas,
            trilha=TrilhaResumoDTO(id=trilha.id, titulo=trilha.titulo),
            proxima_aula=(
                AulaResumoDTO(
                    id=proxima.id,
                    titulo=proxima.titulo,
                    duracao_minutos=proxima.duracao_minutos,
                    ordem=proxima.ordem,
                    concluida=proxima.id in concluidas,
                )
                if proxima
                else None
            ),
        )
