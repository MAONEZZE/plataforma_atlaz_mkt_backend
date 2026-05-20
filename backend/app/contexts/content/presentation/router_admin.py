from uuid import UUID

from fastapi import APIRouter, Depends
from starlette import status

from app.contexts.auth.domain.entities import User
from app.contexts.content.application.use_cases.lessons.crud_admin import (
    UpdateLesson,
    CreateLesson,
    DeleteLesson,
    ReorderLessons,
)
from app.contexts.content.application.use_cases.modules.crud_admin import (
    UpdateModule,
    CreateModule,
    DeleteModule,
    ReorderModules,
)
from app.contexts.content.application.use_cases.tracks.crud_admin import (
    UpdateTrack,
    CreateTrack,
    DeleteTrack,
    ReorderTracks,
)
from app.contexts.content.domain.exceptions import (
    LessonNotFound,
    InvalidDriveUrl,
    ModuleNotFound,
    TrackNotFound,
)
from app.contexts.content.presentation.deps import (
    get_update_lesson,
    get_update_module,
    get_update_track,
    get_create_lesson,
    get_create_module,
    get_create_track,
    get_delete_lesson,
    get_delete_module,
    get_delete_track,
    get_reorder_lessons,
    get_reorder_modules,
    get_reorder_tracks,
)
from app.contexts.content.presentation.schemas import (
    UpdateLessonIn,
    UpdateModuleIn,
    UpdateTrackIn,
    AulaAdminOut,
    CreateLessonIn,
    CreateModuleIn,
    CreateTrackIn,
    ModuloAdminOut,
    ReordenarIn,
    TrilhaAdminOut,
)
from app.core.deps import require_admin
from app.core.exceptions import AppException

router = APIRouter(prefix="/admin", tags=["admin-conteudo"])


# ── Trilhas ────────────────────────────────────────────────────────────────────


@router.post("/trilhas", response_model=TrilhaAdminOut, status_code=status.HTTP_201_CREATED)
async def criar_trilha(
    body: CreateTrackIn,
    _: User = Depends(require_admin),
    use_case: CreateTrack = Depends(get_create_track),
) -> TrackAdminOut:
    trilha = await use_case.execute(body.titulo, body.descricao, body.capa_url, body.ordem)
    return TrilhaAdminOut(
        id=trilha.id,
        titulo=trilha.titulo,
        descricao=trilha.descricao,
        capa_url=trilha.capa_url,
        ordem=trilha.ordem,
        criado_em=trilha.criado_em,
    )


@router.patch("/trilhas/{trilha_id}", response_model=TrilhaAdminOut)
async def atualizar_trilha(
    trilha_id: UUID,
    body: UpdateTrackIn,
    _: User = Depends(require_admin),
    use_case: UpdateTrack = Depends(get_update_track),
) -> TrackAdminOut:
    try:
        trilha = await use_case.execute(
            trilha_id, body.titulo, body.descricao, body.capa_url, body.ordem
        )
    except TrackNotFound as exc:
        raise AppException("TRILHA_NOT_FOUND", str(exc), 404) from exc
    return TrilhaAdminOut(
        id=trilha.id,
        titulo=trilha.titulo,
        descricao=trilha.descricao,
        capa_url=trilha.capa_url,
        ordem=trilha.ordem,
        criado_em=trilha.criado_em,
    )


@router.delete("/trilhas/{trilha_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remover_trilha(
    trilha_id: UUID,
    _: User = Depends(require_admin),
    use_case: DeleteTrack = Depends(get_delete_track),
) -> None:
    try:
        await use_case.execute(trilha_id)
    except TrackNotFound as exc:
        raise AppException("TRILHA_NOT_FOUND", str(exc), 404) from exc


@router.post("/trilhas/reordenar", status_code=status.HTTP_204_NO_CONTENT)
async def reordenar_trilhas(
    body: ReordenarIn,
    _: User = Depends(require_admin),
    use_case: ReorderTracks = Depends(get_reorder_tracks),
) -> None:
    await use_case.execute([(item.id, item.ordem) for item in body.ordem])


# ── Módulos ────────────────────────────────────────────────────────────────────


@router.post("/modulos", response_model=ModuloAdminOut, status_code=status.HTTP_201_CREATED)
async def criar_modulo(
    body: CreateModuleIn,
    _: User = Depends(require_admin),
    use_case: CreateModule = Depends(get_create_module),
) -> ModuleAdminOut:
    modulo = await use_case.execute(body.trilha_id, body.titulo, body.descricao, body.ordem)
    return ModuloAdminOut(
        id=modulo.id,
        trilha_id=modulo.trilha_id,
        titulo=modulo.titulo,
        descricao=modulo.descricao,
        ordem=modulo.ordem,
    )


@router.patch("/modulos/{modulo_id}", response_model=ModuloAdminOut)
async def atualizar_modulo(
    modulo_id: UUID,
    body: UpdateModuleIn,
    _: User = Depends(require_admin),
    use_case: UpdateModule = Depends(get_update_module),
) -> ModuleAdminOut:
    try:
        modulo = await use_case.execute(modulo_id, body.titulo, body.descricao, body.ordem)
    except ModuleNotFound as exc:
        raise AppException("MODULO_NOT_FOUND", str(exc), 404) from exc
    return ModuloAdminOut(
        id=modulo.id,
        trilha_id=modulo.trilha_id,
        titulo=modulo.titulo,
        descricao=modulo.descricao,
        ordem=modulo.ordem,
    )


@router.delete("/modulos/{modulo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remover_modulo(
    modulo_id: UUID,
    _: User = Depends(require_admin),
    use_case: DeleteModule = Depends(get_delete_module),
) -> None:
    try:
        await use_case.execute(modulo_id)
    except ModuleNotFound as exc:
        raise AppException("MODULO_NOT_FOUND", str(exc), 404) from exc


@router.post("/modulos/reordenar", status_code=status.HTTP_204_NO_CONTENT)
async def reordenar_modulos(
    body: ReordenarIn,
    _: User = Depends(require_admin),
    use_case: ReorderModules = Depends(get_reorder_modules),
) -> None:
    await use_case.execute([(item.id, item.ordem) for item in body.ordem])


# ── Aulas ──────────────────────────────────────────────────────────────────────


@router.post("/aulas", response_model=AulaAdminOut, status_code=status.HTTP_201_CREATED)
async def criar_aula(
    body: CreateLessonIn,
    _: User = Depends(require_admin),
    use_case: CreateLesson = Depends(get_create_lesson),
) -> LessonAdminOut:
    try:
        aula = await use_case.execute(
            body.modulo_id,
            body.titulo,
            body.descricao,
            body.drive_url,
            body.duracao_minutos,
            body.ordem,
        )
    except InvalidDriveUrl as exc:
        raise AppException("DRIVE_URL_INVALID", str(exc), 400) from exc
    return AulaAdminOut(
        id=aula.id,
        modulo_id=aula.modulo_id,
        titulo=aula.titulo,
        descricao=aula.descricao,
        drive_file_id=aula.drive_file_id,
        duracao_minutos=aula.duracao_minutos,
        ordem=aula.ordem,
        criado_em=aula.criado_em,
    )


@router.patch("/aulas/{aula_id}", response_model=AulaAdminOut)
async def atualizar_aula(
    aula_id: UUID,
    body: UpdateLessonIn,
    _: User = Depends(require_admin),
    use_case: UpdateLesson = Depends(get_update_lesson),
) -> LessonAdminOut:
    try:
        aula = await use_case.execute(
            aula_id,
            body.titulo,
            body.descricao,
            body.drive_url,
            body.duracao_minutos,
            body.ordem,
        )
    except LessonNotFound as exc:
        raise AppException("AULA_NOT_FOUND", str(exc), 404) from exc
    except InvalidDriveUrl as exc:
        raise AppException("DRIVE_URL_INVALID", str(exc), 400) from exc
    return AulaAdminOut(
        id=aula.id,
        modulo_id=aula.modulo_id,
        titulo=aula.titulo,
        descricao=aula.descricao,
        drive_file_id=aula.drive_file_id,
        duracao_minutos=aula.duracao_minutos,
        ordem=aula.ordem,
        criado_em=aula.criado_em,
    )


@router.delete("/aulas/{aula_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remover_aula(
    aula_id: UUID,
    _: User = Depends(require_admin),
    use_case: DeleteLesson = Depends(get_delete_lesson),
) -> None:
    try:
        await use_case.execute(aula_id)
    except LessonNotFound as exc:
        raise AppException("AULA_NOT_FOUND", str(exc), 404) from exc


@router.post("/aulas/reordenar", status_code=status.HTTP_204_NO_CONTENT)
async def reordenar_aulas(
    body: ReordenarIn,
    _: User = Depends(require_admin),
    use_case: ReorderLessons = Depends(get_reorder_lessons),
) -> None:
    await use_case.execute([(item.id, item.ordem) for item in body.ordem])
