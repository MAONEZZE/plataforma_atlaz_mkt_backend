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
    ModuleWithLessonsOut,
    TrackSummaryOut,
    TrackWithModulesOut,
    TrackProgressOut,
)
from app.core.deps import get_current_user
from app.core.exceptions import AppException

router = APIRouter(tags=["content"])


@router.get("/tracks", response_model=list[TrackProgressOut])
async def list_tracks(
    user: User = Depends(get_current_user),
    use_case: ListTracksWithProgress = Depends(get_list_tracks),
) -> list[TrackProgressOut]:
    dtos = await use_case.execute(user.id)
    return [
        TrackProgressOut(
            id=d.id,
            title=d.title,
            description=d.description,
            cover_url=d.cover_url,
            total_lessons=d.total_lessons,
            lessons_completed=d.lessons_completed,
            progress_pct=d.progress_pct,
        )
        for d in dtos
    ]


@router.get("/tracks/{track_id}", response_model=TrackWithModulesOut)
async def get_track(
    track_id: UUID,
    user: User = Depends(get_current_user),
    use_case: GetTrackWithModules = Depends(get_track_with_modules),
) -> TrackWithModulesOut:
    try:
        dto = await use_case.execute(track_id, user.id)
    except TrackNotFound as exc:
        raise AppException("TRILHA_NOT_FOUND", str(exc), 404) from exc
    return TrackWithModulesOut(
        id=dto.id,
        title=dto.title,
        description=dto.description,
        cover_url=dto.cover_url,
        progress_pct=dto.progress_pct,
        modules=[
            ModuleWithLessonsOut(
                id=m.id,
                title=m.title,
                description=m.description,
                order=m.order,
                lessons=[
                    LessonSummaryOut(
                        id=a.id,
                        title=a.title,
                        duration_minutes=a.duration_minutes,
                        order=a.order,
                        completed=a.completed,
                    )
                    for a in m.lessons
                ],
            )
            for m in dto.modules
        ],
    )


@router.get("/lessons/{lesson_id}", response_model=LessonDetailOut)
async def get_lesson(
    lesson_id: UUID,
    user: User = Depends(get_current_user),
    use_case: GetLesson = Depends(get_lesson),
) -> LessonDetailOut:
    try:
        dto = await use_case.execute(lesson_id, user.id)
    except LessonNotFound as exc:
        raise AppException("AULA_NOT_FOUND", str(exc), 404) from exc
    except (ModuleNotFound, TrackNotFound) as exc:
        raise AppException("INTERNAL_ERROR", str(exc), 500) from exc
    return LessonDetailOut(
        id=dto.id,
        module_id=dto.module_id,
        title=dto.title,
        description=dto.description,
        drive_file_id=dto.drive_file_id,
        duration_minutes=dto.duration_minutes,
        completed=dto.completed,
        track=TrackSummaryOut(id=dto.track.id, title=dto.track.title),
        next_lesson=(
            LessonSummaryOut(
                id=dto.next_lesson.id,
                title=dto.next_lesson.title,
                duration_minutes=dto.next_lesson.duration_minutes,
                order=dto.next_lesson.order,
                completed=dto.next_lesson.completed,
            )
            if dto.next_lesson
            else None
        ),
    )


@router.post(
    "/lessons/{lesson_id}/complete",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def mark_lesson_completed(
    lesson_id: UUID,
    user: User = Depends(get_current_user),
    use_case: MarkCompleted = Depends(get_mark_completed),
) -> None:
    try:
        await use_case.execute(lesson_id, user.id)
    except LessonNotFound as exc:
        raise AppException("AULA_NOT_FOUND", str(exc), 404) from exc


@router.delete(
    "/lessons/{lesson_id}/complete",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def unmark_lesson_completed(
    lesson_id: UUID,
    user: User = Depends(get_current_user),
    use_case: Unmark = Depends(get_unmark),
) -> None:
    await use_case.execute(lesson_id, user.id)
