from uuid import UUID

from app.contexts.content.application.dtos import (
    LessonSummaryDTO,
    ModuleWithLessonsDTO,
    TrackWithModulesDTO,
)
from app.contexts.content.domain.exceptions import TrackNotFound
from app.contexts.content.domain.repositories import (
    AlunoAulaRepository,
    AulaRepository,
    ModuloRepository,
    TrilhaRepository,
)


class GetTrackWithModules:
    def __init__(
        self,
        trilha_repo: TrackRepository,
        modulo_repo: ModuleRepository,
        aula_repo: LessonRepository,
        aluno_aula_repo: AlunoAulaRepository,
    ) -> None:
        self._trilha_repo = trilha_repo
        self._modulo_repo = modulo_repo
        self._aula_repo = aula_repo
        self._aluno_aula_repo = aluno_aula_repo

    async def execute(self, trilha_id: UUID, usuario_id: UUID) -> TrackComModulosDTO:
        trilha = await self._trilha_repo.get_by_id(trilha_id)
        if trilha is None:
            raise TrackNotFound(f"Trilha {trilha_id} não encontrada.")

        concluidas = await self._aluno_aula_repo.completed_ids(usuario_id)
        modulos = await self._modulo_repo.list_by_track(trilha_id)

        total_aulas = 0
        concluidas_count = 0
        modulos_dto = []

        for modulo in modulos:
            aulas = await self._aula_repo.list_by_module(modulo.id)
            total_aulas += len(aulas)
            concluidas_count += sum(1 for a in aulas if a.id in concluidas)

            modulos_dto.append(
                ModuleWithLessonsDTO(
                    id=modulo.id,
                    titulo=modulo.titulo,
                    descricao=modulo.descricao,
                    ordem=modulo.ordem,
                    aulas=[
                        LessonSummaryDTO(
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

        return TrackWithModulesDTO(
            id=trilha.id,
            titulo=trilha.titulo,
            descricao=trilha.descricao,
            capa_url=trilha.capa_url,
            progresso_pct=pct,
            modulos=modulos_dto,
        )
