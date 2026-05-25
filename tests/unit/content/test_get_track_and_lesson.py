from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from app.domain.content_module.content_exceptions import LessonNotFound, TrackNotFound
from app.domain.content_module.content_model import Lesson, Module, Track
from app.services.content_module.lessons.get import GetLesson
from app.services.content_module.tracks.get_with_modules import (
    GetTrackWithModules,
)

# ── Fake repos ─────────────────────────────────────────────────────────────────

class FakeTrackRepo:
    def __init__(self, tracks: list[Track] | None = None) -> None:
        self._tracks = tracks or []

    async def list_all(self) -> list[Track]:
        return list(self._tracks)

    async def get_by_id(self, track_id: UUID) -> Track | None:
        return next((t for t in self._tracks if t.id == track_id), None)


class FakeModuleRepo:
    def __init__(self, modules: list[Module] | None = None) -> None:
        self._modules = modules or []

    async def list_by_track(self, track_id: UUID) -> list[Module]:
        return [m for m in self._modules if m.track_id == track_id]

    async def get_by_id(self, module_id: UUID) -> Module | None:
        return next((m for m in self._modules if m.id == module_id), None)


class FakeLessonRepo:
    def __init__(self, lessons: list[Lesson] | None = None) -> None:
        self._lessons = lessons or []

    async def get_by_id(self, lesson_id: UUID) -> Lesson | None:
        return next((a for a in self._lessons if a.id == lesson_id), None)

    async def list_by_module(self, module_id: UUID) -> list[Lesson]:
        return [a for a in self._lessons if a.module_id == module_id]

    async def next_lesson(self, lesson: Lesson) -> Lesson | None:
        same_module = sorted(
            [a for a in self._lessons if a.module_id == lesson.module_id and a.order > lesson.order],
            key=lambda a: a.order,
        )
        return same_module[0] if same_module else None


class FakeStudentLessonRepo:
    def __init__(self, completeds: set[UUID] | None = None) -> None:
        self._completeds: set[UUID] = completeds or set()

    async def completed_ids(self, user_id: UUID) -> set[UUID]:
        return self._completeds


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_track() -> Track:
    return Track(
        id=uuid4(), title="T", description=None, cover_url=None,
        order=0, created_at=datetime.now(tz=UTC)
    )


def _make_module(track_id: UUID, order: int = 0) -> Module:
    return Module(id=uuid4(), track_id=track_id, title="M", description=None, order=order)


def _make_lesson(module_id: UUID, order: int = 0) -> Lesson:
    return Lesson(
        id=uuid4(), module_id=module_id, title="A", description=None,
        drive_file_id="x", duration_minutes=None, order=order, created_at=datetime.now(tz=UTC)
    )


# ── GetTrackWithModules ──────────────────────────────────────────────────────

async def test_get_track_not_found_raises() -> None:
    use_case = GetTrackWithModules(
        FakeTrackRepo(), FakeModuleRepo(), FakeLessonRepo(), FakeStudentLessonRepo()
    )
    with pytest.raises(TrackNotFound):
        await use_case.execute(uuid4(), uuid4())


async def test_get_track_with_modules_structure() -> None:
    track = _make_track()
    module = _make_module(track.id)
    lesson = _make_lesson(module.id)

    use_case = GetTrackWithModules(
        FakeTrackRepo([track]),
        FakeModuleRepo([module]),
        FakeLessonRepo([lesson]),
        FakeStudentLessonRepo({lesson.id}),
    )
    dto = await use_case.execute(track.id, uuid4())

    assert dto.id == track.id
    assert len(dto.modules) == 1
    assert len(dto.modules[0].lessons) == 1
    assert dto.modules[0].lessons[0].completed is True
    assert dto.progress_pct == 100.0


async def test_get_track_progress_zero() -> None:
    track = _make_track()
    module = _make_module(track.id)
    lesson = _make_lesson(module.id)

    use_case = GetTrackWithModules(
        FakeTrackRepo([track]),
        FakeModuleRepo([module]),
        FakeLessonRepo([lesson]),
        FakeStudentLessonRepo(),
    )
    dto = await use_case.execute(track.id, uuid4())
    assert dto.progress_pct == 0.0
    assert dto.modules[0].lessons[0].completed is False


# ── GetLesson ──────────────────────────────────────────────────────────────────

async def test_get_lesson_not_found_raises() -> None:
    use_case = GetLesson(FakeLessonRepo(), FakeModuleRepo(), FakeTrackRepo(), FakeStudentLessonRepo())
    with pytest.raises(LessonNotFound):
        await use_case.execute(uuid4(), uuid4())


async def test_get_lesson_with_next_lesson() -> None:
    track = _make_track()
    module = _make_module(track.id)
    lesson1 = _make_lesson(module.id, order=0)
    lesson2 = _make_lesson(module.id, order=1)

    use_case = GetLesson(
        FakeLessonRepo([lesson1, lesson2]),
        FakeModuleRepo([module]),
        FakeTrackRepo([track]),
        FakeStudentLessonRepo(),
    )
    dto = await use_case.execute(lesson1.id, uuid4())
    assert dto.next_lesson is not None
    assert dto.next_lesson.id == lesson2.id


async def test_get_last_lesson_next_lesson_none() -> None:
    track = _make_track()
    module = _make_module(track.id)
    lesson = _make_lesson(module.id)

    use_case = GetLesson(
        FakeLessonRepo([lesson]),
        FakeModuleRepo([module]),
        FakeTrackRepo([track]),
        FakeStudentLessonRepo(),
    )
    dto = await use_case.execute(lesson.id, uuid4())
    assert dto.next_lesson is None


async def test_get_lesson_completed_flag() -> None:
    track = _make_track()
    module = _make_module(track.id)
    lesson = _make_lesson(module.id)

    use_case = GetLesson(
        FakeLessonRepo([lesson]),
        FakeModuleRepo([module]),
        FakeTrackRepo([track]),
        FakeStudentLessonRepo({lesson.id}),
    )
    dto = await use_case.execute(lesson.id, uuid4())
    assert dto.completed is True
    assert dto.track.id == track.id


# ── Mapper EN attribute regression (Fix #1) ────────────────────────────────────

def test_track_model_exposes_en_attributes() -> None:
    """TrackModel must have EN Python attrs so mapper doesn't raise AttributeError."""
    from app.database.content_module.content_repo import TrackModel, _track_from_model

    now = datetime.now(tz=UTC)
    m = TrackModel(id=uuid4(), title="T", description="D", cover_url=None, order=2, created_at=now)
    assert m.title == "T"
    assert m.description == "D"
    assert m.order == 2
    track = _track_from_model(m)
    assert track.title == "T"
    assert track.order == 2


def test_module_model_exposes_en_attributes() -> None:
    from app.database.content_module.content_repo import ModuleModel, _module_from_model

    tid = uuid4()
    m = ModuleModel(id=uuid4(), track_id=tid, title="M", description=None, order=1)
    assert m.title == "M"
    assert m.order == 1
    module = _module_from_model(m)
    assert module.title == "M"
    assert module.track_id == tid


def test_lesson_model_exposes_en_attributes() -> None:
    from app.database.content_module.content_repo import LessonModel, _lesson_from_model

    now = datetime.now(tz=UTC)
    m = LessonModel(
        id=uuid4(), module_id=uuid4(), title="L", description=None,
        drive_file_id="abc", duration_minutes=30, order=0, created_at=now,
    )
    assert m.title == "L"
    assert m.duration_minutes == 30
    lesson = _lesson_from_model(m)
    assert lesson.title == "L"
    assert lesson.duration_minutes == 30


def test_comment_model_exposes_en_attributes() -> None:
    from app.database.content_module.content_repo import CommentModel, _comment_from_model

    now = datetime.now(tz=UTC)
    m = CommentModel(
        id=uuid4(), lesson_id=uuid4(), user_id=uuid4(),
        text="hello", created_at=now, edited_at=None, deleted_at=None,
    )
    assert m.text == "hello"
    comment = _comment_from_model(m)
    assert comment.text == "hello"
