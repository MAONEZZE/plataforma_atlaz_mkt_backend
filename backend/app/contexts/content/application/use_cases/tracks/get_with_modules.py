from uuid import UUID

from app.contexts.conteudo.application.dtos import (
    AulaResumoDTO,
    ModuloComAulasDTO,
    TrilhaComModulosDTO,
)
from app.contexts.conteudo.domain.exceptions import TrilhaNaoEncontrada
from app.contexts.conteudo.domain.repositories import (
    AlunoAulaRepository,
    AulaRepository,
    ModuloRepository,
    TrilhaRepository,
)


class ObterTrilhaComModulos:
    def __init__(
        self,
        trilha_repo: TrilhaRepository,
        modulo_repo: ModuloRepository,
        aula_repo: AulaRepository,
        aluno_aula_repo: AlunoAulaRepository,
    ) -> None:
        self._trilha_repo = trilha_repo
        self._modulo_repo = modulo_repo
        self._aula_repo = aula_repo
        self._aluno_aula_repo = aluno_aula_repo

    async def execute(self, trilha_id: UUID, usuario_id: UUID) -> TrilhaComModulosDTO:
        trilha = await self._trilha_repo.por_id(trilha_id)
        if trilha is None:
            raise TrilhaNaoEncontrada(f"Trilha {trilha_id} não encontrada.")

        concluidas = await self._aluno_aula_repo.concluidas_ids(usuario_id)
        modulos = await self._modulo_repo.listar_por_trilha(trilha_id)

        total_aulas = 0
        concluidas_count = 0
        modulos_dto = []

        for modulo in modulos:
            aulas = await self._aula_repo.listar_por_modulo(modulo.id)
            total_aulas += len(aulas)
            concluidas_count += sum(1 for a in aulas if a.id in concluidas)

            modulos_dto.append(
                ModuloComAulasDTO(
                    id=modulo.id,
                    titulo=modulo.titulo,
                    descricao=modulo.descricao,
                    ordem=modulo.ordem,
                    aulas=[
                        AulaResumoDTO(
                            id=a.id,
                            titulo=a.titulo,
                            duracao_minutos=a.duracao_minutos,
                            ordem=a.ordem,
                            concluida=a.id in concluidas,
                        )
                        for a in aulas
                    ],
                )
            )

        pct = round(concluidas_count / total_aulas * 100, 2) if total_aulas > 0 else 0.0

        return TrilhaComModulosDTO(
            id=trilha.id,
            titulo=trilha.titulo,
            descricao=trilha.descricao,
            capa_url=trilha.capa_url,
            progresso_pct=pct,
            modulos=modulos_dto,
        )
