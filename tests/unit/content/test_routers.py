"""HTTP-layer tests using FastAPI TestClient with dependency overrides."""
from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.config.dependencies.auth_deps import get_current_user, require_admin
from app.api.controllers.content_module.content_dto.content_dto import (
    AuthorDTO,
    CommentDTO,
    LessonDetailDTO,
    ModuleWithLessonsDTO,
    TrackProgressDTO,
    TrackSummaryDTO,
    TrackWithModulesDTO,
)
from app.api.controllers.content_module.content_routes.content_router import (
    get_create_lesson,
    get_create_module,
    get_create_track,
    get_delete_comment,
    get_delete_module,
    get_delete_track,
    get_edit_comment,
    get_lesson,
    get_list_comments,
    get_list_tracks,
    get_mark_completed,
    get_reorder_lessons,
    get_reorder_modules,
    get_reorder_tracks,
    get_track_with_modules,
    get_unmark,
    get_update_module,
    get_update_track,
)
from app.domain.auth_module.auth_model import User
from app.domain.content_module.content_exceptions import (
    CommentNotFound,
    CommentNotOwnedByUser,
    InvalidDriveUrl,
    LessonNotFound,
    ModuleNotFound,
    TrackNotFound,
)
from app.domain.content_module.content_model import Lesson, Module, Track
from app.domain.shared.dtos import PagedResponse
from app.main import app

# ── Auth helpers ───────────────────────────────────────────────────────────────

def _client_user(user_id: UUID | None = None) -> User:
    return User(id=user_id or uuid4(), email="user@test.com", role="cliente", inactive=False)


def _admin_user(user_id: UUID | None = None) -> User:
    return User(id=user_id or uuid4(), email="admin@test.com", role="admin", inactive=False)


def _mock_uc(**kwargs: object) -> AsyncMock:
    """Return an AsyncMock with .execute returning kwargs value."""
    m = AsyncMock()
    if "execute_return" in kwargs:
        m.execute.return_value = kwargs["execute_return"]
    elif "execute_raises" in kwargs:
        m.execute.side_effect = kwargs["execute_raises"]
    return m


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture
def client() -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


def _base_track(track_id: UUID | None = None) -> Track:
    return Track(
        id=track_id or uuid4(), title="T", description=None, cover_url=None,
        order=0, created_at=datetime.now(tz=UTC)
    )


def _base_lesson(lesson_id: UUID | None = None, module_id: UUID | None = None) -> Lesson:
    return Lesson(
        id=lesson_id or uuid4(), module_id=module_id or uuid4(), title="A",
        description=None, drive_file_id="abc", duration_minutes=None,
        order=0, created_at=datetime.now(tz=UTC)
    )


def _base_module(module_id: UUID | None = None, track_id: UUID | None = None) -> Module:
    return Module(
        id=module_id or uuid4(), track_id=track_id or uuid4(),
        title="M", description=None, order=0
    )


# ── GET /tracks ────────────────────────────────────────────────────────────────

def test_list_tracks_returns_200(client: TestClient) -> None:
    user = _client_user()
    track_id = uuid4()
    dto = TrackProgressDTO(
        id=track_id, title="T", description=None, cover_url=None,
        total_lessons=5, lessons_completed=2, progress_pct=40.0
    )
    uc = _mock_uc(execute_return=[dto])
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_list_tracks] = lambda: uc
    try:
        r = client.get("/api/v1/tracks")
        assert r.status_code == 200
        assert r.json()[0]["progress_pct"] == 40.0
    finally:
        app.dependency_overrides.clear()


def test_list_tracks_requires_auth(client: TestClient) -> None:
    r = client.get("/api/v1/tracks")
    assert r.status_code == 401


# ── GET /tracks/{id} ───────────────────────────────────────────────────────────

def test_get_track_returns_200(client: TestClient) -> None:
    user = _client_user()
    track_id = uuid4()
    dto = TrackWithModulesDTO(
        id=track_id, title="T", description=None, cover_url=None,
        progress_pct=0.0,
        modules=[
            ModuleWithLessonsDTO(id=uuid4(), title="M", description=None, order=0, lessons=[])
        ],
    )
    uc = _mock_uc(execute_return=dto)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_track_with_modules] = lambda: uc
    try:
        r = client.get(f"/api/v1/tracks/{track_id}")
        assert r.status_code == 200
        assert r.json()["id"] == str(track_id)
    finally:
        app.dependency_overrides.clear()


def test_get_track_404(client: TestClient) -> None:
    user = _client_user()
    uc = _mock_uc(execute_raises=TrackNotFound("not found"))
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_track_with_modules] = lambda: uc
    try:
        r = client.get(f"/api/v1/tracks/{uuid4()}")
        assert r.status_code == 404
    finally:
        app.dependency_overrides.clear()


# ── GET /lessons/{id} ─────────────────────────────────────────────────────────

def test_get_lesson_returns_200(client: TestClient) -> None:
    user = _client_user()
    lesson_id = uuid4()
    dto = LessonDetailDTO(
        id=lesson_id, module_id=uuid4(), title="A", description=None,
        drive_file_id="abc", duration_minutes=None, completed=False,
        track=TrackSummaryDTO(id=uuid4(), title="T"),
        next_lesson=None,
    )
    uc = _mock_uc(execute_return=dto)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_lesson] = lambda: uc
    try:
        r = client.get(f"/api/v1/lessons/{lesson_id}")
        assert r.status_code == 200
        assert r.json()["next_lesson"] is None
    finally:
        app.dependency_overrides.clear()


def test_get_lesson_404(client: TestClient) -> None:
    user = _client_user()
    uc = _mock_uc(execute_raises=LessonNotFound("nope"))
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_lesson] = lambda: uc
    try:
        r = client.get(f"/api/v1/lessons/{uuid4()}")
        assert r.status_code == 404
    finally:
        app.dependency_overrides.clear()


# ── POST /lessons/{id}/complete ────────────────────────────────────────────────

def test_mark_completed_204(client: TestClient) -> None:
    user = _client_user()
    uc = _mock_uc(execute_return=None)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_mark_completed] = lambda: uc
    try:
        r = client.post(f"/api/v1/lessons/{uuid4()}/complete")
        assert r.status_code == 204
    finally:
        app.dependency_overrides.clear()


def test_unmark_completed_204(client: TestClient) -> None:
    user = _client_user()
    uc = _mock_uc(execute_return=None)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_unmark] = lambda: uc
    try:
        r = client.delete(f"/api/v1/lessons/{uuid4()}/complete")
        assert r.status_code == 204
    finally:
        app.dependency_overrides.clear()


# ── Admin tracks ───────────────────────────────────────────────────────────────

def test_admin_create_track_201(client: TestClient) -> None:
    user = _admin_user()
    track = _base_track()
    uc = _mock_uc(execute_return=track)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[require_admin] = lambda: user
    app.dependency_overrides[get_create_track] = lambda: uc
    try:
        r = client.post("/api/v1/admin/tracks", json={"title": "T"})
        assert r.status_code == 201
    finally:
        app.dependency_overrides.clear()


def test_admin_create_track_requires_admin(client: TestClient) -> None:
    user = _client_user()
    app.dependency_overrides[get_current_user] = lambda: user
    try:
        r = client.post("/api/v1/admin/tracks", json={"title": "T"})
        assert r.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_admin_delete_track_404(client: TestClient) -> None:
    user = _admin_user()
    uc = _mock_uc(execute_raises=TrackNotFound("nope"))
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[require_admin] = lambda: user
    app.dependency_overrides[get_delete_track] = lambda: uc
    try:
        r = client.delete(f"/api/v1/admin/tracks/{uuid4()}")
        assert r.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_admin_reorder_tracks_204(client: TestClient) -> None:
    user = _admin_user()
    uc = _mock_uc(execute_return=None)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[require_admin] = lambda: user
    app.dependency_overrides[get_reorder_tracks] = lambda: uc
    try:
        r = client.post(
            "/api/v1/admin/tracks/reorder",
            json={"order": [{"id": str(uuid4()), "order": 0}]},
        )
        assert r.status_code == 204
    finally:
        app.dependency_overrides.clear()


# ── Admin modules ──────────────────────────────────────────────────────────────

def test_admin_create_module_201(client: TestClient) -> None:
    user = _admin_user()
    module = _base_module()
    uc = _mock_uc(execute_return=module)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[require_admin] = lambda: user
    app.dependency_overrides[get_create_module] = lambda: uc
    try:
        r = client.post(
            "/api/v1/admin/modules",
            json={"track_id": str(uuid4()), "title": "M"},
        )
        assert r.status_code == 201
    finally:
        app.dependency_overrides.clear()


def test_admin_delete_module_404(client: TestClient) -> None:
    user = _admin_user()
    uc = _mock_uc(execute_raises=ModuleNotFound("nope"))
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[require_admin] = lambda: user
    app.dependency_overrides[get_delete_module] = lambda: uc
    try:
        r = client.delete(f"/api/v1/admin/modules/{uuid4()}")
        assert r.status_code == 404
    finally:
        app.dependency_overrides.clear()


# ── Admin lessons ──────────────────────────────────────────────────────────────

def test_admin_create_lesson_invalid_drive_url_400(client: TestClient) -> None:
    user = _admin_user()
    uc = _mock_uc(execute_raises=InvalidDriveUrl("bad-url"))
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[require_admin] = lambda: user
    app.dependency_overrides[get_create_lesson] = lambda: uc
    try:
        r = client.post(
            "/api/v1/admin/lessons",
            json={
                "module_id": str(uuid4()),
                "title": "A",
                "drive_url": "bad",
            },
        )
        assert r.status_code == 400
        assert r.json()["error"]["code"] == "DRIVE_URL_INVALID"
    finally:
        app.dependency_overrides.clear()


def test_admin_create_lesson_201(client: TestClient) -> None:
    user = _admin_user()
    lesson = _base_lesson()
    uc = _mock_uc(execute_return=lesson)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[require_admin] = lambda: user
    app.dependency_overrides[get_create_lesson] = lambda: uc
    try:
        r = client.post(
            "/api/v1/admin/lessons",
            json={
                "module_id": str(uuid4()),
                "title": "Lesson",
                "drive_url": "https://drive.google.com/file/d/abc/view",
            },
        )
        assert r.status_code == 201
    finally:
        app.dependency_overrides.clear()


def test_admin_reorder_lessons_204(client: TestClient) -> None:
    user = _admin_user()
    uc = _mock_uc(execute_return=None)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[require_admin] = lambda: user
    app.dependency_overrides[get_reorder_lessons] = lambda: uc
    try:
        r = client.post(
            "/api/v1/admin/lessons/reorder",
            json={"order": [{"id": str(uuid4()), "order": 0}]},
        )
        assert r.status_code == 204
    finally:
        app.dependency_overrides.clear()


# ── Comments ───────────────────────────────────────────────────────────────────

def test_list_comments_200(client: TestClient) -> None:
    user = _client_user()
    now = datetime.now(tz=UTC)
    paged: PagedResponse[CommentDTO] = PagedResponse(
        items=[
            CommentDTO(
                id=uuid4(),
                author=AuthorDTO(id=uuid4(), name="Alice", photo_url=None),
                text="Great!",
                created_at=now,
                edited_at=None,
                deleted_at=None,
                is_own=False,
            )
        ],
        page=1,
        page_size=20,
        total=1,
    )
    uc = _mock_uc(execute_return=paged)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_list_comments] = lambda: uc
    try:
        r = client.get(f"/api/v1/lessons/{uuid4()}/comments")
        assert r.status_code == 200
        assert r.json()["total"] == 1
    finally:
        app.dependency_overrides.clear()


def test_create_comment_text_too_long_400(client: TestClient) -> None:
    user = _client_user()
    app.dependency_overrides[get_current_user] = lambda: user
    try:
        r = client.post(
            f"/api/v1/lessons/{uuid4()}/comments",
            json={"text": "x" * 2001},
        )
        assert r.status_code == 400
    finally:
        app.dependency_overrides.clear()


def test_edit_comment_403(client: TestClient) -> None:
    user = _client_user()
    uc = _mock_uc(execute_raises=CommentNotOwnedByUser("no permission"))
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_edit_comment] = lambda: uc
    try:
        r = client.patch(f"/api/v1/comments/{uuid4()}", json={"text": "hack"})
        assert r.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_delete_comment_404(client: TestClient) -> None:
    user = _client_user()
    uc = _mock_uc(execute_raises=CommentNotFound("nope"))
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_delete_comment] = lambda: uc
    try:
        r = client.delete(f"/api/v1/comments/{uuid4()}")
        assert r.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_delete_comment_204(client: TestClient) -> None:
    user = _client_user()
    uc = _mock_uc(execute_return=None)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_delete_comment] = lambda: uc
    try:
        r = client.delete(f"/api/v1/comments/{uuid4()}")
        assert r.status_code == 204
    finally:
        app.dependency_overrides.clear()


def test_admin_update_track_404(client: TestClient) -> None:
    user = _admin_user()
    uc = _mock_uc(execute_raises=TrackNotFound("nope"))
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[require_admin] = lambda: user
    app.dependency_overrides[get_update_track] = lambda: uc
    try:
        r = client.patch(f"/api/v1/admin/tracks/{uuid4()}", json={"title": "X"})
        assert r.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_admin_update_module_404(client: TestClient) -> None:
    user = _admin_user()
    uc = _mock_uc(execute_raises=ModuleNotFound("nope"))
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[require_admin] = lambda: user
    app.dependency_overrides[get_update_module] = lambda: uc
    try:
        r = client.patch(f"/api/v1/admin/modules/{uuid4()}", json={"title": "X"})
        assert r.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_admin_reorder_modules_204(client: TestClient) -> None:
    user = _admin_user()
    uc = _mock_uc(execute_return=None)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[require_admin] = lambda: user
    app.dependency_overrides[get_reorder_modules] = lambda: uc
    try:
        r = client.post(
            "/api/v1/admin/modules/reorder",
            json={"order": [{"id": str(uuid4()), "order": 0}]},
        )
        assert r.status_code == 204
    finally:
        app.dependency_overrides.clear()


def test_create_track_handles_domain_error(client: TestClient) -> None:
    """create_track must return 404, not 500, when service raises TrackNotFound (Fix #6)."""
    user = _admin_user()
    uc = _mock_uc(execute_raises=TrackNotFound("not found"))
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[require_admin] = lambda: user
    app.dependency_overrides[get_create_track] = lambda: uc
    try:
        r = client.post("/api/v1/admin/tracks", json={"title": "T"})
        assert r.status_code == 404
        assert r.json()["error"]["code"] == "TRILHA_NOT_FOUND"
    finally:
        app.dependency_overrides.clear()


def test_create_module_handles_domain_error(client: TestClient) -> None:
    """create_module must return 404, not 500, when service raises ModuleNotFound (Fix #6)."""
    user = _admin_user()
    uc = _mock_uc(execute_raises=ModuleNotFound("not found"))
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[require_admin] = lambda: user
    app.dependency_overrides[get_create_module] = lambda: uc
    try:
        r = client.post(
            "/api/v1/admin/modules",
            json={"track_id": str(uuid4()), "title": "M", "order": 0},
        )
        assert r.status_code == 404
        assert r.json()["error"]["code"] == "MODULO_NOT_FOUND"
    finally:
        app.dependency_overrides.clear()
