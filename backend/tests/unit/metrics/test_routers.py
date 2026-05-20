"""HTTP-layer tests using FastAPI TestClient with dependency overrides."""
from datetime import UTC, date, datetime
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.config.dependencies.auth_deps import get_current_user, require_admin
from app.api.controllers.metrics_module.metrics_dto.metrics_dto import (
    AdminAggregatesDTO,
    AdminConsolidatedDTO,
    DashboardSeriesDTO,
    DashboardSummaryDTO,
    DeltaDTO,
    MetricDTO,
    UserMonthlyMetricsDTO,
    WeeklySeriesDTO,
)
from app.api.controllers.metrics_module.metrics_routes.metrics_router import (
    get_admin_consolidated,
    get_create_metric,
    get_dashboard_series,
    get_dashboard_summary,
    get_list_metrics,
    get_update_metric,
)
from app.domain.auth_module.auth_model import User
from app.domain.metrics_module.metrics_exceptions import (
    DuplicateMetric,
    FutureWeekNotAllowed,
    MetricNotFound,
    MetricNotOwnedByUser,
    MetricOutOfWindow,
)
from app.main import app


def _cliente(user_id: UUID | None = None) -> User:
    return User(id=user_id or uuid4(), email="u@test.com", role="cliente", inactive=False)


def _admin(user_id: UUID | None = None) -> User:
    return User(id=user_id or uuid4(), email="a@test.com", role="admin", inactive=False)


def _mock_uc(**kwargs: object) -> AsyncMock:
    m = AsyncMock()
    if "execute_return" in kwargs:
        m.execute.return_value = kwargs["execute_return"]
    elif "execute_raises" in kwargs:
        m.execute.side_effect = kwargs["execute_raises"]
    return m


def _metrica_dto(user_id: UUID | None = None) -> MetricDTO:
    now = datetime.now(tz=UTC)
    return MetricDTO(
        id=uuid4(),
        user_id=user_id or uuid4(),
        week_start=date(2026, 5, 11),
        calls_scheduled=10,
        calls_made=8,
        meetings_scheduled=3,
        referrals=1,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def client() -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


# ── GET /metricas ──────────────────────────────────────────────────────────────

def test_listar_metricas_200(client: TestClient) -> None:
    user = _cliente()
    from app.domain.shared.dtos import PagedResponse
    paged = PagedResponse(items=[_metrica_dto(user.id)], page=1, page_size=20, total=1)
    uc = _mock_uc(execute_return=paged)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_list_metrics] = lambda: uc
    try:
        r = client.get("/api/v1/metricas")
        assert r.status_code == 200
        assert r.json()["total"] == 1
    finally:
        app.dependency_overrides.clear()


def test_listar_metricas_requires_auth(client: TestClient) -> None:
    r = client.get("/api/v1/metricas")
    assert r.status_code == 401


# ── POST /metricas ─────────────────────────────────────────────────────────────

def test_criar_metrica_201(client: TestClient) -> None:
    user = _cliente()
    dto = _metrica_dto(user.id)
    uc = _mock_uc(execute_return=dto)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_create_metric] = lambda: uc
    try:
        r = client.post(
            "/api/v1/metricas",
            json={
                "week_start": "2026-05-11",
                "calls_scheduled": 10,
                "calls_made": 8,
                "meetings_scheduled": 3,
                "referrals": 1,
            },
        )
        assert r.status_code == 201
        assert r.json()["week_start"] == "2026-05-11"
    finally:
        app.dependency_overrides.clear()


def test_criar_metrica_409_duplicate(client: TestClient) -> None:
    user = _cliente()
    uc = _mock_uc(execute_raises=DuplicateMetric("dup"))
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_create_metric] = lambda: uc
    try:
        r = client.post(
            "/api/v1/metricas",
            json={
                "week_start": "2026-05-11",
                "calls_scheduled": 0,
                "calls_made": 0,
                "meetings_scheduled": 0,
                "referrals": 0,
            },
        )
        assert r.status_code == 409
        assert r.json()["error"]["code"] == "METRICA_DUPLICADA"
    finally:
        app.dependency_overrides.clear()


def test_criar_metrica_422_fora_da_janela(client: TestClient) -> None:
    user = _cliente()
    uc = _mock_uc(execute_raises=MetricOutOfWindow("janela"))
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_create_metric] = lambda: uc
    try:
        r = client.post(
            "/api/v1/metricas",
            json={
                "week_start": "2026-01-05",
                "calls_scheduled": 0,
                "calls_made": 0,
                "meetings_scheduled": 0,
                "referrals": 0,
            },
        )
        assert r.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_criar_metrica_422_semana_futura(client: TestClient) -> None:
    user = _cliente()
    uc = _mock_uc(execute_raises=FutureWeekNotAllowed("futura"))
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_create_metric] = lambda: uc
    try:
        r = client.post(
            "/api/v1/metricas",
            json={
                "week_start": "2026-06-01",
                "calls_scheduled": 0,
                "calls_made": 0,
                "meetings_scheduled": 0,
                "referrals": 0,
            },
        )
        assert r.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_criar_metrica_403_para_outro_usuario(client: TestClient) -> None:
    user = _cliente()
    app.dependency_overrides[get_current_user] = lambda: user
    try:
        r = client.post(
            "/api/v1/metricas",
            json={
                "user_id": str(uuid4()),  # different user
                "week_start": "2026-05-11",
                "calls_scheduled": 0,
                "calls_made": 0,
                "meetings_scheduled": 0,
                "referrals": 0,
            },
        )
        assert r.status_code == 403
    finally:
        app.dependency_overrides.clear()


# ── PATCH /metricas/{id} ───────────────────────────────────────────────────────

def test_atualizar_metrica_200(client: TestClient) -> None:
    user = _cliente()
    dto = _metrica_dto(user.id)
    uc = _mock_uc(execute_return=dto)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_update_metric] = lambda: uc
    try:
        r = client.patch(f"/api/v1/metricas/{uuid4()}", json={"calls_scheduled": 20})
        assert r.status_code == 200
    finally:
        app.dependency_overrides.clear()


def test_atualizar_metrica_404(client: TestClient) -> None:
    user = _cliente()
    uc = _mock_uc(execute_raises=MetricNotFound("nope"))
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_update_metric] = lambda: uc
    try:
        r = client.patch(f"/api/v1/metricas/{uuid4()}", json={"calls_scheduled": 5})
        assert r.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_atualizar_metrica_403_wrong_owner(client: TestClient) -> None:
    user = _cliente()
    uc = _mock_uc(execute_raises=MetricNotOwnedByUser("not yours"))
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_update_metric] = lambda: uc
    try:
        r = client.patch(f"/api/v1/metricas/{uuid4()}", json={"calls_scheduled": 5})
        assert r.status_code == 403
    finally:
        app.dependency_overrides.clear()


# ── GET /dashboard/resumo ──────────────────────────────────────────────────────

def test_obter_resumo_200(client: TestClient) -> None:
    user = _cliente()
    dto = DashboardSummaryDTO(
        month="2026-05",
        calls_scheduled=DeltaDTO(value=120, delta_pct=20.0),
        calls_made=DeltaDTO(value=95, delta_pct=None),
        meetings_scheduled=DeltaDTO(value=28, delta_pct=40.0),
        referrals=DeltaDTO(value=12, delta_pct=None),
    )
    uc = _mock_uc(execute_return=dto)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_dashboard_summary] = lambda: uc
    try:
        r = client.get("/api/v1/dashboard/resumo")
        assert r.status_code == 200
        body = r.json()
        assert body["month"] == "2026-05"
        assert body["calls_made"]["delta_pct"] is None
    finally:
        app.dependency_overrides.clear()


def test_obter_resumo_requires_auth(client: TestClient) -> None:
    r = client.get("/api/v1/dashboard/resumo")
    assert r.status_code == 401


# ── GET /dashboard/series ──────────────────────────────────────────────────────

def test_obter_series_200(client: TestClient) -> None:
    user = _cliente()
    dto = DashboardSeriesDTO(
        series=[
            WeeklySeriesDTO(
                week=date(2026, 5, 11),
                calls_scheduled=10,
                calls_made=8,
                meetings_scheduled=3,
                referrals=1,
            )
        ]
    )
    uc = _mock_uc(execute_return=dto)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_dashboard_series] = lambda: uc
    try:
        r = client.get("/api/v1/dashboard/series?semanas=1")
        assert r.status_code == 200
        assert len(r.json()["series"]) == 1
    finally:
        app.dependency_overrides.clear()


# ── GET /admin/dashboard ───────────────────────────────────────────────────────

def test_admin_dashboard_200(client: TestClient) -> None:
    admin = _admin()
    dto = AdminConsolidatedDTO(
        aggregates=AdminAggregatesDTO(
            calls_scheduled_total=100,
            calls_made_total=80,
            meetings_scheduled_total=20,
            referrals_total=5,
            users_with_metric_in_month=3,
            users_without_metric_in_month=2,
        ),
        items=[
            UserMonthlyMetricsDTO(
                user_id=uuid4(),
                name="Alice",
                photo_url=None,
                calls_scheduled=100,
                calls_made=80,
                meetings_scheduled=20,
                referrals=5,
                last_metric_at=date(2026, 5, 4),
            )
        ],
        page=1,
        page_size=20,
        total=1,
    )
    uc = _mock_uc(execute_return=dto)
    app.dependency_overrides[get_current_user] = lambda: admin
    app.dependency_overrides[require_admin] = lambda: admin
    app.dependency_overrides[get_admin_consolidated] = lambda: uc
    try:
        r = client.get("/api/v1/admin/dashboard")
        assert r.status_code == 200
        body = r.json()
        assert body["aggregates"]["users_with_metric_in_month"] == 3
        assert body["items"][0]["name"] == "Alice"
    finally:
        app.dependency_overrides.clear()


def test_admin_dashboard_403_for_cliente(client: TestClient) -> None:
    user = _cliente()
    app.dependency_overrides[get_current_user] = lambda: user
    try:
        r = client.get("/api/v1/admin/dashboard")
        assert r.status_code == 403
    finally:
        app.dependency_overrides.clear()
