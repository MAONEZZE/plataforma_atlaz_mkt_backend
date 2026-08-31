from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from app.domain.content_module.content_exceptions import (
    InvalidDriveUrl,
    LessonNotFound,
    ModuleNotFound,
)
from app.domain.content_module.content_model import Lesson, Module
from app.services.content_module.lessons.crud_admin import (
    CreateLesson,
    DeleteLesson,
    UpdateLesson,
)
from app.services.content_module.lessons.mark_completed import MarkCompleted
from app.services.content_module.lessons.unmark import Unmark

# ── Fake repos ─────────────────────────────────────────────────────────────────

class FakeLessonRepo:
    def __init__(self, lessons: list[Lesson] | None = None) -> None:
        self._lessons: list[Lesson] = lessons or []

    async def get_by_id(self, lesson_id: UUID) -> Lesson | None:
        return next((a for a in self._lessons if a.id == lesson_id), None)

    async def list_by_module(self, module_id: UUID) -> list[Lesson]:
        return [a for a in self._lessons if a.module_id == module_id]

    async def create(self, lesson: Lesson) -> Lesson:
        self._lessons.append(lesson)
        return lesson

    async def update(self, lesson: Lesson) -> Lesson:
        self._lessons = [lesson if a.id == lesson.id else a for a in self._lessons]
        return lesson

    async def delete(self, lesson_id: UUID) -> None:
        self._lessons = [a for a in self._lessons if a.id != lesson_id]


class FakeModuleRepo:
    def __init__(self, modules: list[Module] | None = None) -> None:
        self._modules: list[Module] = modules or []

    async def get_by_id(self, module_id: UUID) -> Module | None:
        return next((m for m in self._modules if m.id == module_id), None)


class FakeStudentLessonRepo:
    def __init__(self) -> None:
        self._completeds: set[tuple[UUID, UUID]] = set()

    async def mark_completed(self, user_id: UUID, lesson_id: UUID) -> None:
        self._completeds.add((user_id, lesson_id))

    async def unmark(self, user_id: UUID, lesson_id: UUID) -> None:
        self._completeds.discard((user_id, lesson_id))

    async def completed_ids(self, user_id: UUID) -> set[UUID]:
        return {lesson_id for uid, lesson_id in self._completeds if uid == user_id}


def _make_lesson(
    drive_file_id: str = "abc123",
    is_doc: bool = False,
    module_id: UUID | None = None,
    order: int = 0,
) -> Lesson:
    return Lesson(
        id=uuid4(),
        module_id=module_id or uuid4(),
        title="Lesson",
        description=None,
        drive_file_id=drive_file_id,
        duration_minutes=None,
        order=order,
        is_doc=is_doc,
        created_at=datetime.now(tz=UTC),
    )


# ── CreateLesson ──────────────────────────────────────────────────────────────

async def test_create_lesson_extracts_drive_id() -> None:
    repo = FakeLessonRepo()
    use_case = CreateLesson(repo)
    lesson = await use_case.execute(
        uuid4(), "Title", None, "https://drive.google.com/file/d/abc123/view", None, None, 0, False
    )
    assert lesson.drive_file_id == "abc123"


async def test_create_lesson_invalid_drive_url_raises() -> None:
    repo = FakeLessonRepo()
    use_case = CreateLesson(repo)
    with pytest.raises(InvalidDriveUrl):
        await use_case.execute(uuid4(), "T", None, "https://example.com/bad", None, None, 0, False)


# ── UpdateLesson ──────────────────────────────────────────────────────────────

async def test_update_lesson_not_found_raises() -> None:
    repo = FakeLessonRepo()
    use_case = UpdateLesson(repo, FakeModuleRepo())
    with pytest.raises(LessonNotFound):
        await use_case.execute(uuid4(), None, None, None, None, None, None, None)


async def test_update_lesson_updates_drive_url() -> None:
    lesson = _make_lesson()
    repo = FakeLessonRepo([lesson])
    use_case = UpdateLesson(repo, FakeModuleRepo())
    updated = await use_case.execute(
        lesson.id, None, None, "https://drive.google.com/file/d/newid/view", None, None, None, None
    )
    assert updated.drive_file_id == "newid"
    assert updated.module_id == lesson.module_id


async def test_update_lesson_moves_to_other_module_appending_at_end() -> None:
    target = Module(id=uuid4(), track_id=uuid4(), title="Destino", description=None, order=0)
    lesson = _make_lesson(order=7)
    existing = [_make_lesson(module_id=target.id, order=i) for i in range(3)]
    repo = FakeLessonRepo([lesson, *existing])
    use_case = UpdateLesson(repo, FakeModuleRepo([target]))

    updated = await use_case.execute(
        lesson.id, None, None, None, None, None, None, None, target.id
    )

    assert updated.module_id == target.id
    assert updated.order == 3


async def test_update_lesson_move_respects_explicit_order() -> None:
    target = Module(id=uuid4(), track_id=uuid4(), title="Destino", description=None, order=0)
    lesson = _make_lesson(order=7)
    repo = FakeLessonRepo([lesson, _make_lesson(module_id=target.id, order=0)])
    use_case = UpdateLesson(repo, FakeModuleRepo([target]))

    updated = await use_case.execute(
        lesson.id, None, None, None, None, None, 0, None, target.id
    )

    assert updated.module_id == target.id
    assert updated.order == 0


async def test_update_lesson_unknown_module_raises() -> None:
    lesson = _make_lesson()
    use_case = UpdateLesson(FakeLessonRepo([lesson]), FakeModuleRepo())
    with pytest.raises(ModuleNotFound):
        await use_case.execute(
            lesson.id, None, None, None, None, None, None, None, uuid4()
        )


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


async def test_unmark_persists() -> None:
    """After unmark, completed_ids must not contain the lesson (Fix #5 regression)."""
    lesson = _make_lesson()
    lesson_repo = FakeLessonRepo([lesson])
    student_repo = FakeStudentLessonRepo()
    user_id = uuid4()

    mark_uc = MarkCompleted(lesson_repo, student_repo)
    unmark_uc = Unmark(student_repo)

    await mark_uc.execute(lesson.id, user_id)
    assert lesson.id in await student_repo.completed_ids(user_id)

    await unmark_uc.execute(lesson.id, user_id)
    assert lesson.id not in await student_repo.completed_ids(user_id)
