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
    LessonAdminOut,
    CreateLessonIn,
    CreateModuleIn,
    CreateTrackIn,
    ModuleAdminOut,
    ReorderIn,
    TrackAdminOut,
)
from app.core.deps import require_admin
from app.core.exceptions import AppException

router = APIRouter(prefix="/admin", tags=["admin-conteudo"])


# ── Trilhas ────────────────────────────────────────────────────────────────────


@router.post("/tracks", response_model=TrackAdminOut, status_code=status.HTTP_201_CREATED)
async def criar_trilha(
    body: CreateTrackIn,
    _: User = Depends(require_admin),
    use_case: CreateTrack = Depends(get_create_track),
) -> TrackAdminOut:
    track = await use_case.execute(body.title, body.description, body.cover_url, body.order)
    return TrackAdminOut(
        id=track.id,
        title=track.title,
        description=track.description,
        cover_url=track.cover_url,
        order=track.order,
        created_at=track.created_at,
    )


@router.patch("/tracks/{track_id}", response_model=TrackAdminOut)
async def atualizar_trilha(
    track_id: UUID,
    body: UpdateTrackIn,
    _: User = Depends(require_admin),
    use_case: UpdateTrack = Depends(get_update_track),
) -> TrackAdminOut:
    try:
        track = await use_case.execute(
            track_id, body.title, body.description, body.cover_url, body.order
        )
    except TrackNotFound as exc:
        raise AppException("TRILHA_NOT_FOUND", str(exc), 404) from exc
    return TrackAdminOut(
        id=track.id,
        title=track.title,
        description=track.description,
        cover_url=track.cover_url,
        order=track.order,
        created_at=track.created_at,
    )


@router.delete("/tracks/{track_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remover_trilha(
    track_id: UUID,
    _: User = Depends(require_admin),
    use_case: DeleteTrack = Depends(get_delete_track),
) -> None:
    try:
        await use_case.execute(track_id)
    except TrackNotFound as exc:
        raise AppException("TRILHA_NOT_FOUND", str(exc), 404) from exc


@router.post("/tracks/reorder", status_code=status.HTTP_204_NO_CONTENT)
async def reordenar_trilhas(
    body: ReorderIn,
    _: User = Depends(require_admin),
    use_case: ReorderTracks = Depends(get_reorder_tracks),
) -> None:
    await use_case.execute([(item.id, item.order) for item in body.order])


# ── Módulos ────────────────────────────────────────────────────────────────────


@router.post("/modules", response_model=ModuleAdminOut, status_code=status.HTTP_201_CREATED)
async def criar_modulo(
    body: CreateModuleIn,
    _: User = Depends(require_admin),
    use_case: CreateModule = Depends(get_create_module),
) -> ModuleAdminOut:
    module = await use_case.execute(body.track_id, body.title, body.description, body.order)
    return ModuleAdminOut(
        id=module.id,
        track_id=module.track_id,
        title=module.title,
        description=module.description,
        order=module.order,
    )


@router.patch("/modules/{module_id}", response_model=ModuleAdminOut)
async def atualizar_modulo(
    module_id: UUID,
    body: UpdateModuleIn,
    _: User = Depends(require_admin),
    use_case: UpdateModule = Depends(get_update_module),
) -> ModuleAdminOut:
    try:
        module = await use_case.execute(module_id, body.title, body.description, body.order)
    except ModuleNotFound as exc:
        raise AppException("MODULO_NOT_FOUND", str(exc), 404) from exc
    return ModuleAdminOut(
        id=module.id,
        track_id=module.track_id,
        title=module.title,
        description=module.description,
        order=module.order,
    )


@router.delete("/modules/{module_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remover_modulo(
    module_id: UUID,
    _: User = Depends(require_admin),
    use_case: DeleteModule = Depends(get_delete_module),
) -> None:
    try:
        await use_case.execute(module_id)
    except ModuleNotFound as exc:
        raise AppException("MODULO_NOT_FOUND", str(exc), 404) from exc


@router.post("/modules/reorder", status_code=status.HTTP_204_NO_CONTENT)
async def reordenar_modulos(
    body: ReorderIn,
    _: User = Depends(require_admin),
    use_case: ReorderModules = Depends(get_reorder_modules),
) -> None:
    await use_case.execute([(item.id, item.order) for item in body.order])


# ── Aulas ──────────────────────────────────────────────────────────────────────


@router.post("/lessons", response_model=LessonAdminOut, status_code=status.HTTP_201_CREATED)
async def criar_aula(
    body: CreateLessonIn,
    _: User = Depends(require_admin),
    use_case: CreateLesson = Depends(get_create_lesson),
) -> LessonAdminOut:
    try:
        lesson = await use_case.execute(
            body.module_id,
            body.title,
            body.description,
            body.drive_url,
            body.duration_minutes,
            body.order,
        )
    except InvalidDriveUrl as exc:
        raise AppException("DRIVE_URL_INVALID", str(exc), 400) from exc
    return LessonAdminOut(
        id=lesson.id,
        module_id=lesson.module_id,
        title=lesson.title,
        description=lesson.description,
        drive_file_id=lesson.drive_file_id,
        duration_minutes=lesson.duration_minutes,
        order=lesson.order,
        created_at=lesson.created_at,
    )


@router.patch("/lessons/{lesson_id}", response_model=LessonAdminOut)
async def atualizar_aula(
    lesson_id: UUID,
    body: UpdateLessonIn,
    _: User = Depends(require_admin),
    use_case: UpdateLesson = Depends(get_update_lesson),
) -> LessonAdminOut:
    try:
        lesson = await use_case.execute(
            lesson_id,
            body.title,
            body.description,
            body.drive_url,
            body.duration_minutes,
            body.order,
        )
    except LessonNotFound as exc:
        raise AppException("AULA_NOT_FOUND", str(exc), 404) from exc
    except InvalidDriveUrl as exc:
        raise AppException("DRIVE_URL_INVALID", str(exc), 400) from exc
    return LessonAdminOut(
        id=lesson.id,
        module_id=lesson.module_id,
        title=lesson.title,
        description=lesson.description,
        drive_file_id=lesson.drive_file_id,
        duration_minutes=lesson.duration_minutes,
        order=lesson.order,
        created_at=lesson.created_at,
    )


@router.delete("/lessons/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remover_aula(
    lesson_id: UUID,
    _: User = Depends(require_admin),
    use_case: DeleteLesson = Depends(get_delete_lesson),
) -> None:
    try:
        await use_case.execute(lesson_id)
    except LessonNotFound as exc:
        raise AppException("AULA_NOT_FOUND", str(exc), 404) from exc


@router.post("/lessons/reorder", status_code=status.HTTP_204_NO_CONTENT)
async def reordenar_aulas(
    body: ReorderIn,
    _: User = Depends(require_admin),
    use_case: ReorderLessons = Depends(get_reorder_lessons),
) -> None:
    await use_case.execute([(item.id, item.order) for item in body.order])
