from uuid import UUID

from fastapi import APIRouter, Depends
from starlette import status

from app.contexts.auth.domain.entities import User
from app.contexts.content.application.use_cases.lessons.unmark import Unmark
from app.contexts.content.application.use_cases.lessons.mark_completed import MarkCompleted
from app.contexts.content.application.use_cases.lessons.get import GetLesson
from app.contexts.content.application.use_cases.tracks.list_with_progress import (
    ListTracksWithProgress,
)
from app.contexts.content.application.use_cases.tracks.get_with_modules import (
    GetTrackWithModules,
)
from app.contexts.content.domain.exceptions import (
    LessonNotFound,
    ModuleNotFound,
    TrackNotFound,
)
from app.contexts.content.presentation.deps import (
    get_unmark,
    get_list_tracks,
    get_mark_completed,
    get_lesson,
    get_track_with_modules,
)
from app.contexts.content.presentation.schemas import (
    LessonDetailOut,
    LessonSummaryOut,
    ModuloComAulasOut,
    TrilhaComModulosOut,
    TrilhaProgressoOut,
    TrilhaResumoOut,
)
from app.core.deps import get_current_user
from app.core.exceptions import AppException

router = APIRouter(tags=["conteudo"])


@router.get("/trilhas", response_model=list[TrilhaProgressoOut])
async def listar_trilhas(
    user: User = Depends(get_current_user),
    use_case: ListTracksWithProgress = Depends(get_list_tracks),
) -> list[TrilhaProgressoOut]:
    dtos = await use_case.execute(user.id)
    return [
        TrilhaProgressoOut(
            id=d.id,
            titulo=d.titulo,
            descricao=d.descricao,
            capa_url=d.capa_url,
            total_aulas=d.total_aulas,
            aulas_concluidas=d.aulas_concluidas,
            progresso_pct=d.progresso_pct,
        )
        for d in dtos
    ]


@router.get("/trilhas/{trilha_id}", response_model=TrilhaComModulosOut)
async def obter_trilha(
    trilha_id: UUID,
    user: User = Depends(get_current_user),
    use_case: GetTrackWithModules = Depends(get_track_with_modules),
) -> TrackWithModulesOut:
    try:
        dto = await use_case.execute(trilha_id, user.id)
    except TrackNotFound as exc:
        raise AppException("TRILHA_NOT_FOUND", str(exc), 404) from exc
    return TrilhaComModulosOut(
        id=dto.id,
        titulo=dto.titulo,
        descricao=dto.descricao,
        capa_url=dto.capa_url,
        progresso_pct=dto.progresso_pct,
        modulos=[
            ModuloComAulasOut(
                id=m.id,
                titulo=m.titulo,
                descricao=m.descricao,
                ordem=m.ordem,
                aulas=[
                    LessonSummaryOut(
                        id=a.id,
                        titulo=a.titulo,
                        duracao_minutos=a.duracao_minutos,
                        ordem=a.ordem,
                        concluida=a.concluida,
                    )
                    for a in m.aulas
                ],
            )
            for m in dto.modulos
        ],
    )


@router.get("/aulas/{aula_id}", response_model=LessonDetailOut)
async def obter_aula(
    aula_id: UUID,
    user: User = Depends(get_current_user),
    use_case: GetLesson = Depends(get_lesson),
) -> LessonDetalheOut:
    try:
        dto = await use_case.execute(aula_id, user.id)
    except LessonNotFound as exc:
        raise AppException("AULA_NOT_FOUND", str(exc), 404) from exc
    except (ModuleNotFound, TrackNotFound) as exc:
        raise AppException("INTERNAL_ERROR", str(exc), 500) from exc
    return LessonDetailOut(
        id=dto.id,
        modulo_id=dto.modulo_id,
        titulo=dto.titulo,
        descricao=dto.descricao,
        drive_file_id=dto.drive_file_id,
        duracao_minutos=dto.duracao_minutos,
        concluida=dto.concluida,
        trilha=TrilhaResumoOut(id=dto.trilha.id, titulo=dto.trilha.titulo),
        proxima_aula=(
            LessonSummaryOut(
                id=dto.proxima_aula.id,
                titulo=dto.proxima_aula.titulo,
                duracao_minutos=dto.proxima_aula.duracao_minutos,
                ordem=dto.proxima_aula.ordem,
                concluida=dto.proxima_aula.concluida,
            )
            if dto.proxima_aula
            else None
        ),
    )


@router.post(
    "/aulas/{aula_id}/concluir",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def mark_completed(
    aula_id: UUID,
    user: User = Depends(get_current_user),
    use_case: MarkCompleted = Depends(get_mark_completed),
) -> None:
    try:
        await use_case.execute(aula_id, user.id)
    except LessonNotFound as exc:
        raise AppException("AULA_NOT_FOUND", str(exc), 404) from exc


@router.delete(
    "/aulas/{aula_id}/concluir",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def desmarcar_concluida(
    aula_id: UUID,
    user: User = Depends(get_current_user),
    use_case: Unmark = Depends(get_unmark),
) -> None:
    await use_case.execute(aula_id, user.id)
