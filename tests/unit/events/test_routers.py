from datetime import UTC, date, datetime
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.config.dependencies.auth_deps import get_current_user, require_admin
from app.api.controllers.event_module.event_routes.admin_router import (
    _create_event,
    _delete_event,
    _delete_events_by_year,
    _list_events,
    _update_event,
    _upload_event_image,
)
from app.api.controllers.event_module.event_routes.event_router import (
    _list_client_events,
)
from app.domain.auth_module.auth_model import User as AuthUser
from app.domain.event_module.event_exceptions import EventNotFound
from app.domain.event_module.event_model import EventDate
from app.domain.user_module.user_exceptions import InvalidPhoto
from app.main import app

NOW = datetime.now(tz=UTC)


def _admin() -> AuthUser:
    return AuthUser(id=uuid4(), email="a@test.com", role="admin", inactive=False)


def _cliente(user_id: UUID | None = None) -> AuthUser:
    return AuthUser(id=user_id or uuid4(), email="c@test.com", role="cliente", inactive=False)


def _uc(**kwargs: object) -> AsyncMock:
    m = AsyncMock()
    if "execute_return" in kwargs:
        m.execute.return_value = kwargs["execute_return"]
    elif "execute_raises" in kwargs:
        m.execute.side_effect = kwargs["execute_raises"]
    return m


def _event(client_id: UUID | None = None, title: str = "Live event") -> EventDate:
    return EventDate(
        id=uuid4(),
        client_id=client_id,
        title=title,
        date=date(2026, 1, 1),
        description=None,
        image_url=None,
        created_at=NOW,
        updated_at=NOW,
    )


@pytest.fixture
def client() -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


# ── POST /admin/events ─────────────────────────────────────────────────────────


def test_create_event_201(client: TestClient) -> None:
    event = _event()
    app.dependency_overrides[require_admin] = _admin
    app.dependency_overrides[_create_event] = lambda: _uc(execute_return=event)
    try:
        r = client.post(
            "/api/v1/admin/events",
            json={"title": "Live event", "date": "2026-01-01"},
        )
        assert r.status_code == 201
        assert r.json()["title"] == "Live event"
        assert r.json()["client_id"] is None
    finally:
        app.dependency_overrides.clear()


def test_create_event_rejects_non_admin(client: TestClient) -> None:
    app.dependency_overrides[get_current_user] = lambda: _cliente()
    try:
        r = client.post(
            "/api/v1/admin/events",
            json={"title": "Live event", "date": "2026-01-01"},
        )
        assert r.status_code == 403
    finally:
        app.dependency_overrides.clear()


# ── GET /admin/events ──────────────────────────────────────────────────────────


def test_list_events_admin_paginated(client: TestClient) -> None:
    events = [_event(), _event(client_id=uuid4())]
    app.dependency_overrides[require_admin] = _admin
    app.dependency_overrides[_list_events] = lambda: _uc(execute_return=(events, 2))
    try:
        r = client.get("/api/v1/admin/events?page=1&page_size=10")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2
    finally:
        app.dependency_overrides.clear()


# ── PATCH /admin/events/{id} ───────────────────────────────────────────────────


def test_update_event_404(client: TestClient) -> None:
    app.dependency_overrides[require_admin] = _admin
    app.dependency_overrides[_update_event] = lambda: _uc(
        execute_raises=EventNotFound("nope")
    )
    try:
        r = client.patch(f"/api/v1/admin/events/{uuid4()}", json={"title": "x"})
        assert r.status_code == 404
        assert r.json()["error"]["code"] == "EVENT_NOT_FOUND"
    finally:
        app.dependency_overrides.clear()


# ── DELETE /admin/events/{id} ──────────────────────────────────────────────────


def test_delete_event_204(client: TestClient) -> None:
    app.dependency_overrides[require_admin] = _admin
    app.dependency_overrides[_delete_event] = lambda: _uc(execute_return=None)
    try:
        r = client.delete(f"/api/v1/admin/events/{uuid4()}")
        assert r.status_code == 204
    finally:
        app.dependency_overrides.clear()


def test_delete_event_404(client: TestClient) -> None:
    app.dependency_overrides[require_admin] = _admin
    app.dependency_overrides[_delete_event] = lambda: _uc(
        execute_raises=EventNotFound("nope")
    )
    try:
        r = client.delete(f"/api/v1/admin/events/{uuid4()}")
        assert r.status_code == 404
    finally:
        app.dependency_overrides.clear()


# ── DELETE /admin/events (bulk by year) ────────────────────────────────────────


def test_delete_events_by_year_general(client: TestClient) -> None:
    app.dependency_overrides[require_admin] = _admin
    app.dependency_overrides[_delete_events_by_year] = lambda: _uc(execute_return=3)
    try:
        r = client.delete("/api/v1/admin/events?year=2026&scope=general")
        assert r.status_code == 200
        assert r.json()["deleted"] == 3
    finally:
        app.dependency_overrides.clear()


def test_delete_events_by_year_clients(client: TestClient) -> None:
    app.dependency_overrides[require_admin] = _admin
    app.dependency_overrides[_delete_events_by_year] = lambda: _uc(execute_return=5)
    try:
        r = client.delete("/api/v1/admin/events?year=2026&scope=clients")
        assert r.status_code == 200
        assert r.json()["deleted"] == 5
    finally:
        app.dependency_overrides.clear()


def test_delete_events_by_year_requires_scope(client: TestClient) -> None:
    app.dependency_overrides[require_admin] = _admin
    app.dependency_overrides[_delete_events_by_year] = lambda: _uc(execute_return=0)
    try:
        r = client.delete("/api/v1/admin/events?year=2026")
        assert r.status_code in (400, 422)
    finally:
        app.dependency_overrides.clear()


def test_delete_events_by_year_rejects_invalid_scope(client: TestClient) -> None:
    app.dependency_overrides[require_admin] = _admin
    app.dependency_overrides[_delete_events_by_year] = lambda: _uc(execute_return=0)
    try:
        r = client.delete("/api/v1/admin/events?year=2026&scope=xpto")
        assert r.status_code in (400, 422)
    finally:
        app.dependency_overrides.clear()


def test_delete_events_by_year_rejects_non_admin(client: TestClient) -> None:
    app.dependency_overrides[get_current_user] = lambda: _cliente()
    try:
        r = client.delete("/api/v1/admin/events?year=2026&scope=all")
        assert r.status_code == 403
    finally:
        app.dependency_overrides.clear()


# ── POST /admin/events/{id}/image ──────────────────────────────────────────────


def test_upload_event_image_invalid_type_400(client: TestClient) -> None:
    import io

    app.dependency_overrides[require_admin] = _admin
    app.dependency_overrides[_upload_event_image] = lambda: _uc(
        execute_raises=InvalidPhoto("Tipo de imagem não suportado.")
    )
    try:
        r = client.post(
            f"/api/v1/admin/events/{uuid4()}/image",
            files={"image": ("doc.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf")},
        )
        assert r.status_code == 400
    finally:
        app.dependency_overrides.clear()


# ── GET /events (client) ───────────────────────────────────────────────────────


def test_list_events_merges_global_and_particular(client: TestClient) -> None:
    user_id = uuid4()
    general = _event(client_id=None, title="General")
    particular = _event(client_id=user_id, title="Mine")
    app.dependency_overrides[get_current_user] = lambda: _cliente(user_id)
    app.dependency_overrides[_list_client_events] = lambda: _uc(
        execute_return=([general, particular], 2)
    )
    try:
        r = client.get("/api/v1/events")
        assert r.status_code == 200
        data = r.json()
        by_title = {item["title"]: item["is_global"] for item in data["items"]}
        assert by_title == {"General": True, "Mine": False}
    finally:
        app.dependency_overrides.clear()


def test_list_events_requires_auth(client: TestClient) -> None:
    r = client.get("/api/v1/events")
    assert r.status_code == 401
