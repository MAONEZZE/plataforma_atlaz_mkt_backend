from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.contexts.content.application.use_cases.lessons.crud_admin import (
    UpdateLesson,
    CreateLesson,
    DeleteLesson,
    ReorderLessons,
)
from app.contexts.content.application.use_cases.lessons.unmark import Unmark
from app.contexts.content.application.use_cases.lessons.mark_completed import MarkCompleted
from app.contexts.content.application.use_cases.lessons.get import GetLesson
from app.contexts.content.application.use_cases.comments.delete import DeleteComment
from app.contexts.content.application.use_cases.comments.create import CreateComment
from app.contexts.content.application.use_cases.comments.edit import EditComment
from app.contexts.content.application.use_cases.comments.list import ListComments
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
from app.contexts.content.application.use_cases.tracks.list_with_progress import (
    ListTracksWithProgress,
)
from app.contexts.content.application.use_cases.tracks.get_with_modules import (
    GetTrackWithModules,
)
from app.contexts.content.infrastructure.repositories import (
    SqlAlchemyStudentLessonRepository,
    SqlAlchemyLessonRepository,
    SqlAlchemyCommentRepository,
    SqlAlchemyModuleRepository,
    SqlAlchemyTrackRepository,
)
from app.core.db import get_session


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
