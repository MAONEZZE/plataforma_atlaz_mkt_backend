from datetime import UTC, date, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.config.dependencies.auth_deps import get_current_user, require_admin
from app.api.controllers.metrics_module.metrics_dto.metrics_dto import SheetDTO
from app.api.controllers.metrics_module.metrics_routes.metrics_router import (
    get_create_metric,
    get_delete_entry,
    get_delete_metric,
    get_list_metrics,
    get_sheet,
    get_update_metric,
    get_upsert_entry,
)
from app.domain.auth_module.auth_model import User
from app.domain.metrics_module.metrics_exceptions import MetricNotFound, MetricNotOwnedByUser
from app.domain.metrics_module.metrics_model import Metric, MetricEntry
from app.main import app

NOW = datetime.now(tz=UTC)


def _admin() -> User:
    return User(id=uuid4(), email="a@test.com", role="admin", inactive=False)


def _cliente() -> User:
    return User(id=uuid4(), email="c@test.com", role="cliente", inactive=False)


def _uc(**kwargs: object) -> AsyncMock:
    m = AsyncMock()
    if "execute_return" in kwargs:
        m.execute.return_value = kwargs["execute_return"]
    elif "execute_raises" in kwargs:
        m.execute.side_effect = kwargs["execute_raises"]
    return m


def _metric(user_id=None) -> Metric:
    return Metric(
        id=uuid4(),
        user_id=user_id or uuid4(),
        name="Calls",
        unit="qtd",
        order=0,
        created_at=NOW,
        updated_at=NOW,
    )


def _entry(value: int = 5) -> MetricEntry:
    return MetricEntry(
        id=uuid4(), metric_id=uuid4(), day=date(2026, 5, 3), value=value, created_at=NOW, updated_at=NOW
    )


def _sheet() -> SheetDTO:
    return SheetDTO(month="2026-05", columns=[_metric()], days=[date(2026, 5, 1)], entries={})


@pytest.fixture
def client() -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


# ── GET /metricas ──────────────────────────────────────────────────────────────

def test_list_metrics_200(client: TestClient) -> None:
    user = _cliente()
    uc = _uc(execute_return=[_metric(user.id), _metric(user.id)])
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_list_metrics] = lambda: uc
    try:
        r = client.get("/api/v1/metricas")
        assert r.status_code == 200
        assert len(r.json()) == 2
    finally:
        app.dependency_overrides.clear()


def test_list_metrics_401(client: TestClient) -> None:
    r = client.get("/api/v1/metricas")
    assert r.status_code == 401


# ── POST /metricas ─────────────────────────────────────────────────────────────

def test_create_metric_201(client: TestClient) -> None:
    user = _cliente()
    uc = _uc(execute_return=_metric(user.id))
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_create_metric] = lambda: uc
    try:
        r = client.post("/api/v1/metricas", json={"name": "Calls"})
        assert r.status_code == 201
        assert r.json()["name"] == "Calls"
    finally:
        app.dependency_overrides.clear()


def test_create_metric_422_empty_name(client: TestClient) -> None:
    user = _cliente()
    app.dependency_overrides[get_current_user] = lambda: user
    try:
        r = client.post("/api/v1/metricas", json={"name": ""})
        assert r.status_code == 400
    finally:
        app.dependency_overrides.clear()


# ── PATCH /metricas/{id} ─────────────────────────────────────────────────────

def test_update_metric_200(client: TestClient) -> None:
    user = _cliente()
    uc = _uc(execute_return=_metric(user.id))
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_update_metric] = lambda: uc
    try:
        r = client.patch(f"/api/v1/metricas/{uuid4()}", json={"name": "New"})
        assert r.status_code == 200
    finally:
        app.dependency_overrides.clear()


def test_update_metric_404(client: TestClient) -> None:
    user = _cliente()
    uc = _uc(execute_raises=MetricNotFound("nope"))
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_update_metric] = lambda: uc
    try:
        r = client.patch(f"/api/v1/metricas/{uuid4()}", json={"name": "x"})
        assert r.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_update_metric_403_not_owned(client: TestClient) -> None:
    user = _cliente()
    uc = _uc(execute_raises=MetricNotOwnedByUser("nope"))
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_update_metric] = lambda: uc
    try:
        r = client.patch(f"/api/v1/metricas/{uuid4()}", json={"name": "x"})
        assert r.status_code == 403
    finally:
        app.dependency_overrides.clear()


# ── DELETE /metricas/{id} ────────────────────────────────────────────────────

def test_delete_metric_204(client: TestClient) -> None:
    user = _cliente()
    uc = _uc(execute_return=None)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_delete_metric] = lambda: uc
    try:
        r = client.delete(f"/api/v1/metricas/{uuid4()}")
        assert r.status_code == 204
    finally:
        app.dependency_overrides.clear()


# ── GET /metricas/planilha ───────────────────────────────────────────────────

def test_my_sheet_200(client: TestClient) -> None:
    user = _cliente()
    uc = _uc(execute_return=_sheet())
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_sheet] = lambda: uc
    try:
        r = client.get("/api/v1/metricas/planilha?mes=2026-05")
        assert r.status_code == 200
        assert r.json()["month"] == "2026-05"
    finally:
        app.dependency_overrides.clear()


# ── PUT /metricas/{id}/valores/{dia} ─────────────────────────────────────────

def test_upsert_entry_200(client: TestClient) -> None:
    user = _cliente()
    uc = _uc(execute_return=_entry(9))
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_upsert_entry] = lambda: uc
    try:
        r = client.put(f"/api/v1/metricas/{uuid4()}/valores/2026-05-03", json={"value": 9})
        assert r.status_code == 200
        assert r.json()["value"] == 9
    finally:
        app.dependency_overrides.clear()


def test_upsert_entry_403_not_owned(client: TestClient) -> None:
    user = _cliente()
    uc = _uc(execute_raises=MetricNotOwnedByUser("nope"))
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_upsert_entry] = lambda: uc
    try:
        r = client.put(f"/api/v1/metricas/{uuid4()}/valores/2026-05-03", json={"value": 1})
        assert r.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_delete_entry_204(client: TestClient) -> None:
    user = _cliente()
    uc = _uc(execute_return=None)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_delete_entry] = lambda: uc
    try:
        r = client.delete(f"/api/v1/metricas/{uuid4()}/valores/2026-05-03")
        assert r.status_code == 204
    finally:
        app.dependency_overrides.clear()


# ── GET /admin/clients/{id}/metricas/planilha ────────────────────────────────

def test_admin_client_sheet_200(client: TestClient) -> None:
    admin = _admin()
    uc = _uc(execute_return=_sheet())
    app.dependency_overrides[require_admin] = lambda: admin
    app.dependency_overrides[get_sheet] = lambda: uc
    try:
        r = client.get(f"/api/v1/admin/clients/{uuid4()}/metricas/planilha?mes=2026-05")
        assert r.status_code == 200
        assert r.json()["month"] == "2026-05"
    finally:
        app.dependency_overrides.clear()


def test_admin_client_sheet_403_for_cliente(client: TestClient) -> None:
    user = _cliente()
    app.dependency_overrides[get_current_user] = lambda: user
    try:
        r = client.get(f"/api/v1/admin/clients/{uuid4()}/metricas/planilha")
        assert r.status_code == 403
    finally:
        app.dependency_overrides.clear()
