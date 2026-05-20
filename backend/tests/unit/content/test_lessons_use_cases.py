from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from app.domain.content_module.content_exceptions import InvalidDriveUrl, LessonNotFound
from app.domain.content_module.content_model import Lesson
from app.services.content_module.content_service.lessons.crud_admin import (
    CreateLesson,
    DeleteLesson,
    UpdateLesson,
)
from app.services.content_module.content_service.lessons.mark_completed import MarkCompleted
from app.services.content_module.content_service.lessons.unmark import Unmark

# ── Fake repos ─────────────────────────────────────────────────────────────────

class FakeLessonRepo:
    def __init__(self, lessons: list[Lesson] | None = None) -> None:
        self._lessons: list[Lesson] = lessons or []

    async def get_by_id(self, lesson_id: UUID) -> Lesson | None:
        return next((a for a in self._lessons if a.id == lesson_id), None)

    async def create(self, lesson: Lesson) -> Lesson:
        self._lessons.append(lesson)
        return lesson

    async def update(self, lesson: Lesson) -> Lesson:
        self._lessons = [lesson if a.id == lesson.id else a for a in self._lessons]
        return lesson

    async def delete(self, lesson_id: UUID) -> None:
        self._lessons = [a for a in self._lessons if a.id != lesson_id]


class FakeStudentLessonRepo:
    def __init__(self) -> None:
        self._completeds: set[tuple[UUID, UUID]] = set()

    async def mark_completed(self, user_id: UUID, lesson_id: UUID) -> None:
        self._completeds.add((user_id, lesson_id))

    async def unmark(self, user_id: UUID, lesson_id: UUID) -> None:
        self._completeds.discard((user_id, lesson_id))

    async def completed_ids(self, user_id: UUID) -> set[UUID]:
        return {lesson_id for uid, lesson_id in self._completeds if uid == user_id}


def _make_lesson(drive_file_id: str = "abc123") -> Lesson:
    return Lesson(
        id=uuid4(),
        module_id=uuid4(),
        title="Lesson",
        description=None,
        drive_file_id=drive_file_id,
        duration_minutes=None,
        order=0,
        created_at=datetime.now(tz=UTC),
    )


# ── CreateLesson ──────────────────────────────────────────────────────────────

async def test_create_lesson_extracts_drive_id() -> None:
    repo = FakeLessonRepo()
    use_case = CreateLesson(repo)
    lesson = await use_case.execute(
        uuid4(), "Title", None, "https://drive.google.com/file/d/abc123/view", None, 0
    )
    assert lesson.drive_file_id == "abc123"


async def test_create_lesson_invalid_drive_url_raises() -> None:
    repo = FakeLessonRepo()
    use_case = CreateLesson(repo)
    with pytest.raises(InvalidDriveUrl):
        await use_case.execute(uuid4(), "T", None, "https://example.com/bad", None, 0)


# ── UpdateLesson ──────────────────────────────────────────────────────────────

async def test_update_lesson_not_found_raises() -> None:
    repo = FakeLessonRepo()
    use_case = UpdateLesson(repo)
    with pytest.raises(LessonNotFound):
        await use_case.execute(uuid4(), None, None, None, None, None)


async def test_update_lesson_updates_drive_url() -> None:
    lesson = _make_lesson()
    repo = FakeLessonRepo([lesson])
    use_case = UpdateLesson(repo)
    updated = await use_case.execute(
        lesson.id, None, None, "https://drive.google.com/file/d/newid/view", None, None
    )
    assert updated.drive_file_id == "newid"


# ── DeleteLesson ────────────────────────────────────────────────────────────────

async def test_delete_lesson_not_found_raises() -> None:
    use_case = DeleteLesson(FakeLessonRepo())
    with pytest.raises(LessonNotFound):
        await use_case.execute(uuid4())


# ── MarkCompleted / Unmark ────────────────────────────────────────────────────

async def test_mark_completed_idempotent() -> None:
    lesson = _make_lesson()
    lesson_repo = FakeLessonRepo([lesson])
    student_repo = FakeStudentLessonRepo()
    use_case = MarkCompleted(lesson_repo, student_repo)
    user_id = uuid4()
    await use_case.execute(lesson.id, user_id)
    await use_case.execute(lesson.id, user_id)
    assert len(student_repo._completeds) == 1


async def test_mark_completed_lesson_not_found_raises() -> None:
    use_case = MarkCompleted(FakeLessonRepo(), FakeStudentLessonRepo())
    with pytest.raises(LessonNotFound):
        await use_case.execute(uuid4(), uuid4())


async def test_unmark_completed_idempotent() -> None:
    student_repo = FakeStudentLessonRepo()
    use_case = Unmark(student_repo)
    user_id = uuid4()
    lesson_id = uuid4()
    # Unmark without marking first should not fail
    await use_case.execute(lesson_id, user_id)
    assert len(student_repo._completeds) == 0
