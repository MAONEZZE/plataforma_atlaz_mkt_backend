from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from app.domain.content_module.content_exceptions import TrackNotFound
from app.domain.content_module.content_model import Lesson, Module, Track
from app.services.content_module.content_service.tracks.crud_admin import (
    CreateTrack,
    DeleteTrack,
    ReorderTracks,
    UpdateTrack,
)
from app.services.content_module.content_service.tracks.list_with_progress import (
    ListTracksWithProgress,
)

# ── Fake repos ─────────────────────────────────────────────────────────────────

class FakeTrackRepo:
    def __init__(self, tracks: list[Track] | None = None) -> None:
        self._tracks: list[Track] = tracks or []
        self.reorder_calls: list[list[tuple[UUID, int]]] = []

    async def list_all(self) -> list[Track]:
        return list(self._tracks)

    async def get_by_id(self, track_id: UUID) -> Track | None:
        return next((t for t in self._tracks if t.id == track_id), None)

    async def create(self, track: Track) -> Track:
        self._tracks.append(track)
        return track

    async def update(self, track: Track) -> Track:
        self._tracks = [track if t.id == track.id else t for t in self._tracks]
        return track

    async def delete(self, track_id: UUID) -> None:
        self._tracks = [t for t in self._tracks if t.id != track_id]

    async def reorder(self, orders: list[tuple[UUID, int]]) -> None:
        self.reorder_calls.append(orders)

    async def count_lessons(self, track_id: UUID) -> int:
        return 0


class FakeModuleRepo:
    def __init__(self, modules: list[Module] | None = None) -> None:
        self._modules = modules or []

    async def list_by_track(self, track_id: UUID) -> list[Module]:
        return [m for m in self._modules if m.track_id == track_id]


class FakeLessonRepo:
    def __init__(self, lessons: list[Lesson] | None = None) -> None:
        self._lessons = lessons or []

    async def list_by_module(self, module_id: UUID) -> list[Lesson]:
        return [a for a in self._lessons if a.module_id == module_id]


class FakeStudentLessonRepo:
    def __init__(self, completeds: set[UUID] | None = None) -> None:
        self._completeds: set[UUID] = completeds or set()

    async def completed_ids(self, user_id: UUID) -> set[UUID]:
        return self._completeds


# ── CreateTrack ────────────────────────────────────────────────────────────────

async def test_create_track_returns_track() -> None:
    repo = FakeTrackRepo()
    use_case = CreateTrack(repo)
    track = await use_case.execute("Prospecting", "desc", None, 0)
    assert track.title == "Prospecting"
    assert track.order == 0
    assert len(repo._tracks) == 1


async def test_create_track_generates_uuid() -> None:
    repo = FakeTrackRepo()
    use_case = CreateTrack(repo)
    t1 = await use_case.execute("T1", None, None, 0)
    t2 = await use_case.execute("T2", None, None, 0)
    assert t1.id != t2.id


# ── UpdateTrack ────────────────────────────────────────────────────────────

def _make_track(title: str = "Track", order: int = 0) -> Track:
    return Track(
        id=uuid4(),
        title=title,
        description=None,
        cover_url=None,
        order=order,
        created_at=datetime.now(tz=UTC),
    )


async def test_update_track_changes_title() -> None:
    track = _make_track("Old")
    repo = FakeTrackRepo([track])
    use_case = UpdateTrack(repo)
    updated = await use_case.execute(track.id, "New", None, None, None)
    assert updated.title == "New"


async def test_update_track_not_found_raises() -> None:
    repo = FakeTrackRepo()
    use_case = UpdateTrack(repo)
    with pytest.raises(TrackNotFound):
        await use_case.execute(uuid4(), "X", None, None, None)


async def test_update_track_keeps_unchanged_fields() -> None:
    track = _make_track("Title", 3)
    repo = FakeTrackRepo([track])
    use_case = UpdateTrack(repo)
    updated = await use_case.execute(track.id, None, "New desc", None, None)
    assert updated.title == "Title"
    assert updated.description == "New desc"
    assert updated.order == 3


# ── DeleteTrack ──────────────────────────────────────────────────────────────

async def test_delete_track_removes_it() -> None:
    track = _make_track()
    repo = FakeTrackRepo([track])
    use_case = DeleteTrack(repo)
    await use_case.execute(track.id)
    assert repo._tracks == []


async def test_delete_track_not_found_raises() -> None:
    repo = FakeTrackRepo()
    use_case = DeleteTrack(repo)
    with pytest.raises(TrackNotFound):
        await use_case.execute(uuid4())


# ── ReorderTracks ───────────────────────────────────────────────────────────

async def test_reorder_tracks_calls_repo() -> None:
    repo = FakeTrackRepo()
    use_case = ReorderTracks(repo)
    id1, id2 = uuid4(), uuid4()
    await use_case.execute([(id1, 0), (id2, 1)])
    assert repo.reorder_calls == [[(id1, 0), (id2, 1)]]


# ── ListTracksWithProgress ──────────────────────────────────────────────────

async def test_list_tracks_progress_zero_lessons() -> None:
    track = _make_track()
    track_repo = FakeTrackRepo([track])
    module_repo = FakeModuleRepo()
    lesson_repo = FakeLessonRepo()
    student_repo = FakeStudentLessonRepo()

    use_case = ListTracksWithProgress(track_repo, module_repo, lesson_repo, student_repo)
    result = await use_case.execute(uuid4())

    assert len(result) == 1
    assert result[0].progress_pct == 0.0
    assert result[0].total_lessons == 0


async def test_list_tracks_progress_partial() -> None:
    track = _make_track()
    module = Module(id=uuid4(), track_id=track.id, title="M1", description=None, order=0)
    lesson1 = Lesson(
        id=uuid4(), module_id=module.id, title="L1", description=None,
        drive_file_id="x", duration_minutes=None, order=0, created_at=datetime.now(tz=UTC)
    )
    lesson2 = Lesson(
        id=uuid4(), module_id=module.id, title="L2", description=None,
        drive_file_id="y", duration_minutes=None, order=1, created_at=datetime.now(tz=UTC)
    )

    track_repo = FakeTrackRepo([track])
    module_repo = FakeModuleRepo([module])
    lesson_repo = FakeLessonRepo([lesson1, lesson2])
    student_repo = FakeStudentLessonRepo({lesson1.id})

    use_case = ListTracksWithProgress(track_repo, module_repo, lesson_repo, student_repo)
    result = await use_case.execute(uuid4())

    assert result[0].lessons_completed == 1
    assert result[0].total_lessons == 2
    assert result[0].progress_pct == 50.0
