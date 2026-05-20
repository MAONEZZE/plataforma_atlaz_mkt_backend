from uuid import UUID

from app.contexts.content.application.dtos import LessonDetailDTO, LessonSummaryDTO, TrackSummaryDTO
from app.contexts.content.domain.exceptions import (
    LessonNotFound,
    ModuleNotFound,
    TrackNotFound,
)
from app.contexts.content.domain.repositories import (
    AlunoAulaRepository,
    AulaRepository,
    ModuloRepository,
    TrilhaRepository,
)


class GetLesson:
    def __init__(
        self,
        aula_repo: LessonRepository,
        modulo_repo: ModuleRepository,
        trilha_repo: TrackRepository,
        aluno_aula_repo: AlunoAulaRepository,
    ) -> None:
        self._aula_repo = aula_repo
        self._modulo_repo = modulo_repo
        self._trilha_repo = trilha_repo
        self._aluno_aula_repo = aluno_aula_repo

    async def execute(self, aula_id: UUID, usuario_id: UUID) -> LessonDetalheDTO:
        aula = await self._aula_repo.get_by_id(aula_id)
        if aula is None:
            raise LessonNotFound(f"Aula {aula_id} não encontrada.")

        modulo = await self._modulo_repo.get_by_id(aula.modulo_id)
        if modulo is None:
            raise ModuleNotFound(f"Módulo {aula.modulo_id} não encontrado.")

        trilha = await self._trilha_repo.get_by_id(modulo.trilha_id)
        if trilha is None:
            raise TrackNotFound(f"Trilha {modulo.trilha_id} não encontrada.")

        concluidas = await self._aluno_aula_repo.completed_ids(usuario_id)
        proxima = await self._aula_repo.next_lesson(aula)

        return LessonDetailDTO(
            id=aula.id,
            modulo_id=aula.modulo_id,
            titulo=aula.titulo,
            descricao=aula.descricao,
            drive_file_id=aula.drive_file_id,
            duracao_minutos=aula.duracao_minutos,
            concluida=aula.id in concluidas,
            trilha=TrackSummaryDTO(id=trilha.id, titulo=trilha.titulo),
            proxima_aula=(
                LessonSummaryDTO(
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
