# Merged from: contexts/content/presentation/deps.py + router_content.py + router_admin.py + router_comments.py
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.api.config.dependencies.auth_deps import get_current_user, require_admin
from app.api.controllers.content_module.content_dto.content_dto import (
    AuthorOut,
    CommentOut,
    CreateCommentIn,
    CreateLessonIn,
    CreateModuleIn,
    CreateTrackIn,
    EditCommentIn,
    LessonAdminOut,
    LessonDetailOut,
    LessonSummaryOut,
    ModuleAdminOut,
    ModuleWithLessonsOut,
    ReorderIn,
    TrackAdminOut,
    TrackProgressOut,
    TrackSummaryOut,
    TrackWithModulesOut,
    UpdateLessonIn,
    UpdateModuleIn,
    UpdateTrackIn,
)
from app.database.content_module.content_repo import (
    SqlAlchemyCommentRepository,
    SqlAlchemyLessonRepository,
    SqlAlchemyModuleRepository,
    SqlAlchemyStudentLessonRepository,
    SqlAlchemyTrackRepository,
)
from app.database.shared.db_factory import get_session
from app.domain.auth_module.auth_model import User as AuthUser
from app.domain.content_module.content_exceptions import (
    CommentNotFound,
    CommentNotOwnedByUser,
    InvalidDriveUrl,
    LessonNotFound,
    ModuleNotFound,
    TrackNotFound,
)
from app.domain.shared.base_exceptions import AppException
from app.services.content_module.content_service.comments.create import CreateComment
from app.services.content_module.content_service.comments.delete import DeleteComment
from app.services.content_module.content_service.comments.edit import EditComment
from app.services.content_module.content_service.comments.list import ListComments
from app.services.content_module.content_service.lessons.crud_admin import (
    CreateLesson,
    DeleteLesson,
    ReorderLessons,
    UpdateLesson,
)
from app.services.content_module.content_service.lessons.get import GetLesson
from app.services.content_module.content_service.lessons.mark_completed import MarkCompleted
from app.services.content_module.content_service.lessons.unmark import Unmark
from app.services.content_module.content_service.modules.crud_admin import (
    CreateModule,
    DeleteModule,
    ReorderModules,
    UpdateModule,
)
from app.services.content_module.content_service.tracks.crud_admin import (
    CreateTrack,
    DeleteTrack,
    ReorderTracks,
    UpdateTrack,
)
from app.services.content_module.content_service.tracks.get_with_modules import GetTrackWithModules
from app.services.content_module.content_service.tracks.list_with_progress import (
    ListTracksWithProgress,
)
from app.shared.application.dtos import PagedResponse

# ── Dependency helpers ─────────────────────────────────────────────────────────


def _repos(session: AsyncSession) -> tuple[
    SqlAlchemyTrackRepository,
    SqlAlchemyModuleRepository,
    SqlAlchemyLessonRepository,
    SqlAlchemyStudentLessonRepository,
    SqlAlchemyCommentRepository,
]:
    return (
        SqlAlchemyTrackRepository(session),
        SqlAlchemyModuleRepository(session),
        SqlAlchemyLessonRepository(session),
        SqlAlchemyStudentLessonRepository(session),
        SqlAlchemyCommentRepository(session),
    )


def get_list_tracks(session: AsyncSession = Depends(get_session)) -> ListTracksWithProgress:
    t, m, a, aa, _ = _repos(session)
    return ListTracksWithProgress(t, m, a, aa)


def get_track_with_modules(session: AsyncSession = Depends(get_session)) -> GetTrackWithModules:
    t, m, a, aa, _ = _repos(session)
    return GetTrackWithModules(t, m, a, aa)


def get_create_track(session: AsyncSession = Depends(get_session)) -> CreateTrack:
    t, _, _, _, _ = _repos(session)
    return CreateTrack(t)


def get_update_track(session: AsyncSession = Depends(get_session)) -> UpdateTrack:
    t, _, _, _, _ = _repos(session)
    return UpdateTrack(t)


def get_delete_track(session: AsyncSession = Depends(get_session)) -> DeleteTrack:
    t, _, _, _, _ = _repos(session)
    return DeleteTrack(t)


def get_reorder_tracks(session: AsyncSession = Depends(get_session)) -> ReorderTracks:
    t, _, _, _, _ = _repos(session)
    return ReorderTracks(t)


def get_create_module(session: AsyncSession = Depends(get_session)) -> CreateModule:
    _, m, _, _, _ = _repos(session)
    return CreateModule(m)


def get_update_module(session: AsyncSession = Depends(get_session)) -> UpdateModule:
    _, m, _, _, _ = _repos(session)
    return UpdateModule(m)


def get_delete_module(session: AsyncSession = Depends(get_session)) -> DeleteModule:
    _, m, _, _, _ = _repos(session)
    return DeleteModule(m)


def get_reorder_modules(session: AsyncSession = Depends(get_session)) -> ReorderModules:
    _, m, _, _, _ = _repos(session)
    return ReorderModules(m)


def get_lesson(session: AsyncSession = Depends(get_session)) -> GetLesson:
    t, m, a, aa, _ = _repos(session)
    return GetLesson(a, m, t, aa)


def get_create_lesson(session: AsyncSession = Depends(get_session)) -> CreateLesson:
    _, _, a, _, _ = _repos(session)
    return CreateLesson(a)


def get_update_lesson(session: AsyncSession = Depends(get_session)) -> UpdateLesson:
    _, _, a, _, _ = _repos(session)
    return UpdateLesson(a)


def get_delete_lesson(session: AsyncSession = Depends(get_session)) -> DeleteLesson:
    _, _, a, _, _ = _repos(session)
    return DeleteLesson(a)


def get_reorder_lessons(session: AsyncSession = Depends(get_session)) -> ReorderLessons:
    _, _, a, _, _ = _repos(session)
    return ReorderLessons(a)


def get_mark_completed(session: AsyncSession = Depends(get_session)) -> MarkCompleted:
    _, _, a, aa, _ = _repos(session)
    return MarkCompleted(a, aa)


def get_unmark(session: AsyncSession = Depends(get_session)) -> Unmark:
    _, _, _, aa, _ = _repos(session)
    return Unmark(aa)


def get_list_comments(session: AsyncSession = Depends(get_session)) -> ListComments:
    _, _, _, _, c = _repos(session)
    return ListComments(c)


def get_create_comment(session: AsyncSession = Depends(get_session)) -> CreateComment:
    _, _, a, _, c = _repos(session)
    return CreateComment(a, c)


def get_edit_comment(session: AsyncSession = Depends(get_session)) -> EditComment:
    _, _, _, _, c = _repos(session)
    return EditComment(c)


def get_delete_comment(session: AsyncSession = Depends(get_session)) -> DeleteComment:
    _, _, _, _, c = _repos(session)
    return DeleteComment(c)


# ── Routers ────────────────────────────────────────────────────────────────────

router = APIRouter(tags=["content"])
admin_router = APIRouter(prefix="/admin", tags=["admin-conteudo"])
comments_router = APIRouter(tags=["comments"])


# ── Content routes ─────────────────────────────────────────────────────────────

@router.get("/tracks", response_model=list[TrackProgressOut])
async def list_tracks(
    user: AuthUser = Depends(get_current_user),
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
    user: AuthUser = Depends(get_current_user),
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
async def get_lesson_endpoint(
    lesson_id: UUID,
    user: AuthUser = Depends(get_current_user),
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
    user: AuthUser = Depends(get_current_user),
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
    user: AuthUser = Depends(get_current_user),
    use_case: Unmark = Depends(get_unmark),
) -> None:
    await use_case.execute(lesson_id, user.id)


# ── Admin routes ───────────────────────────────────────────────────────────────

@admin_router.post("/tracks", response_model=TrackAdminOut, status_code=status.HTTP_201_CREATED)
async def create_track(
    body: CreateTrackIn,
    _: AuthUser = Depends(require_admin),
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


@admin_router.patch("/tracks/{track_id}", response_model=TrackAdminOut)
async def update_track(
    track_id: UUID,
    body: UpdateTrackIn,
    _: AuthUser = Depends(require_admin),
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


@admin_router.delete("/tracks/{track_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_track(
    track_id: UUID,
    _: AuthUser = Depends(require_admin),
    use_case: DeleteTrack = Depends(get_delete_track),
) -> None:
    try:
        await use_case.execute(track_id)
    except TrackNotFound as exc:
        raise AppException("TRILHA_NOT_FOUND", str(exc), 404) from exc


@admin_router.post("/tracks/reorder", status_code=status.HTTP_204_NO_CONTENT)
async def reorder_tracks(
    body: ReorderIn,
    _: AuthUser = Depends(require_admin),
    use_case: ReorderTracks = Depends(get_reorder_tracks),
) -> None:
    await use_case.execute([(item.id, item.order) for item in body.order])


@admin_router.post("/modules", response_model=ModuleAdminOut, status_code=status.HTTP_201_CREATED)
async def create_module(
    body: CreateModuleIn,
    _: AuthUser = Depends(require_admin),
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


@admin_router.patch("/modules/{module_id}", response_model=ModuleAdminOut)
async def update_module(
    module_id: UUID,
    body: UpdateModuleIn,
    _: AuthUser = Depends(require_admin),
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


@admin_router.delete("/modules/{module_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_module(
    module_id: UUID,
    _: AuthUser = Depends(require_admin),
    use_case: DeleteModule = Depends(get_delete_module),
) -> None:
    try:
        await use_case.execute(module_id)
    except ModuleNotFound as exc:
        raise AppException("MODULO_NOT_FOUND", str(exc), 404) from exc


@admin_router.post("/modules/reorder", status_code=status.HTTP_204_NO_CONTENT)
async def reorder_modules(
    body: ReorderIn,
    _: AuthUser = Depends(require_admin),
    use_case: ReorderModules = Depends(get_reorder_modules),
) -> None:
    await use_case.execute([(item.id, item.order) for item in body.order])


@admin_router.post("/lessons", response_model=LessonAdminOut, status_code=status.HTTP_201_CREATED)
async def create_lesson(
    body: CreateLessonIn,
    _: AuthUser = Depends(require_admin),
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


@admin_router.patch("/lessons/{lesson_id}", response_model=LessonAdminOut)
async def update_lesson(
    lesson_id: UUID,
    body: UpdateLessonIn,
    _: AuthUser = Depends(require_admin),
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


@admin_router.delete("/lessons/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lesson(
    lesson_id: UUID,
    _: AuthUser = Depends(require_admin),
    use_case: DeleteLesson = Depends(get_delete_lesson),
) -> None:
    try:
        await use_case.execute(lesson_id)
    except LessonNotFound as exc:
        raise AppException("AULA_NOT_FOUND", str(exc), 404) from exc


@admin_router.post("/lessons/reorder", status_code=status.HTTP_204_NO_CONTENT)
async def reorder_lessons(
    body: ReorderIn,
    _: AuthUser = Depends(require_admin),
    use_case: ReorderLessons = Depends(get_reorder_lessons),
) -> None:
    await use_case.execute([(item.id, item.order) for item in body.order])


# ── Comments routes ────────────────────────────────────────────────────────────

@comments_router.get("/lessons/{lesson_id}/comments", response_model=PagedResponse[CommentOut])
async def list_comments(
    lesson_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: AuthUser = Depends(get_current_user),
    use_case: ListComments = Depends(get_list_comments),
) -> PagedResponse[CommentOut]:
    result = await use_case.execute(lesson_id, page, page_size, user.id)
    return PagedResponse(
        items=[
            CommentOut(
                id=c.id,
                author=AuthorOut(id=c.author.id, name=c.author.name, photo_url=c.author.photo_url),
                text=c.text,
                created_at=c.created_at,
                edited_at=c.edited_at,
                deleted_at=c.deleted_at,
                is_own=c.is_own,
            )
            for c in result.items
        ],
        page=result.page,
        page_size=result.page_size,
        total=result.total,
    )


@comments_router.post(
    "/lessons/{lesson_id}/comments",
    response_model=CommentOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_comment(
    lesson_id: UUID,
    body: CreateCommentIn,
    user: AuthUser = Depends(get_current_user),
    use_case: CreateComment = Depends(get_create_comment),
) -> CommentOut:
    try:
        comment = await use_case.execute(lesson_id, user.id, body.text)
    except LessonNotFound as exc:
        raise AppException("AULA_NOT_FOUND", str(exc), 404) from exc

    return CommentOut(
        id=comment.id,
        author=AuthorOut(id=user.id, name="", photo_url=None),
        text=comment.text,
        created_at=comment.created_at,
        edited_at=comment.edited_at,
        deleted_at=comment.deleted_at,
        is_own=True,
    )


@comments_router.patch("/comments/{comment_id}", response_model=CommentOut)
async def edit_comment(
    comment_id: UUID,
    body: EditCommentIn,
    user: AuthUser = Depends(get_current_user),
    use_case: EditComment = Depends(get_edit_comment),
) -> CommentOut:
    try:
        comment = await use_case.execute(
            comment_id, user.id, user.role == "admin", body.text
        )
    except CommentNotFound as exc:
        raise AppException("COMENTARIO_NOT_FOUND", str(exc), 404) from exc
    except CommentNotOwnedByUser as exc:
        raise AppException("FORBIDDEN", str(exc), 403) from exc
    return CommentOut(
        id=comment.id,
        author=AuthorOut(id=user.id, name="", photo_url=None),
        text=comment.text,
        created_at=comment.created_at,
        edited_at=comment.edited_at,
        deleted_at=comment.deleted_at,
        is_own=True,
    )


@comments_router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: UUID,
    user: AuthUser = Depends(get_current_user),
    use_case: DeleteComment = Depends(get_delete_comment),
) -> None:
    try:
        await use_case.execute(comment_id, user.id, user.role == "admin")
    except CommentNotFound as exc:
        raise AppException("COMENTARIO_NOT_FOUND", str(exc), 404) from exc
    except CommentNotOwnedByUser as exc:
        raise AppException("FORBIDDEN", str(exc), 403) from exc
