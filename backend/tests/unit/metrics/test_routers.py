"""HTTP-layer tests using FastAPI TestClient with dependency overrides."""
from datetime import UTC, date, datetime
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.contexts.auth.domain.entities import Usuario
from app.contexts.metricas.application.dtos import (
    AdminConsolidadoDTO,
    AgregadosAdminDTO,
    DeltaDTO,
    MetricaDTO,
    ResumoDashboardDTO,
    SeriesDashboardDTO,
    SerieSemanalDTO,
    UsuarioMetricasMesDTO,
)
from app.contexts.metricas.domain.exceptions import (
    MetricaDuplicada,
    MetricaForaDaJanela,
    MetricaNaoEncontrada,
    MetricaNaoPertenceAoUsuario,
    SemanaFuturaNaoPermitida,
)
from app.contexts.metricas.presentation.deps import (
    get_admin_consolidado,
    get_atualizar_metrica,
    get_criar_metrica,
    get_listar_metricas,
    get_resumo_dashboard,
    get_series_dashboard,
)
from app.core.deps import get_current_user, require_admin
from app.main import app


def _cliente(user_id: UUID | None = None) -> Usuario:
    return Usuario(id=user_id or uuid4(), email="u@test.com", role="cliente", inativo=False)


def _admin(user_id: UUID | None = None) -> Usuario:
    return Usuario(id=user_id or uuid4(), email="a@test.com", role="admin", inativo=False)


def _mock_uc(**kwargs: object) -> AsyncMock:
    m = AsyncMock()
    if "execute_return" in kwargs:
        m.execute.return_value = kwargs["execute_return"]
    elif "execute_raises" in kwargs:
        m.execute.side_effect = kwargs["execute_raises"]
    return m


def _metrica_dto(user_id: UUID | None = None) -> MetricaDTO:
    now = datetime.now(tz=UTC)
    return MetricaDTO(
        id=uuid4(),
        usuario_id=user_id or uuid4(),
        semana_inicio=date(2026, 5, 11),
        ligacoes_agendadas=10,
        ligacoes_realizadas=8,
        reunioes_agendadas=3,
        indicacoes=1,
        criado_em=now,
        atualizado_em=now,
    )


@pytest.fixture
def client() -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


# ── GET /metricas ──────────────────────────────────────────────────────────────

def test_listar_metricas_200(client: TestClient) -> None:
    user = _cliente()
    from app.shared.application.dtos import PagedResponse
    paged = PagedResponse(items=[_metrica_dto(user.id)], page=1, page_size=20, total=1)
    uc = _mock_uc(execute_return=paged)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_listar_metricas] = lambda: uc
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
    app.dependency_overrides[get_criar_metrica] = lambda: uc
    try:
        r = client.post(
            "/api/v1/metricas",
            json={
                "semana_inicio": "2026-05-11",
                "ligacoes_agendadas": 10,
                "ligacoes_realizadas": 8,
                "reunioes_agendadas": 3,
                "indicacoes": 1,
            },
        )
        assert r.status_code == 201
        assert r.json()["semana_inicio"] == "2026-05-11"
    finally:
        app.dependency_overrides.clear()


def test_criar_metrica_409_duplicate(client: TestClient) -> None:
    user = _cliente()
    uc = _mock_uc(execute_raises=MetricaDuplicada("dup"))
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_criar_metrica] = lambda: uc
    try:
        r = client.post(
            "/api/v1/metricas",
            json={
                "semana_inicio": "2026-05-11",
                "ligacoes_agendadas": 0,
                "ligacoes_realizadas": 0,
                "reunioes_agendadas": 0,
                "indicacoes": 0,
            },
        )
        assert r.status_code == 409
        assert r.json()["error"]["code"] == "METRICA_DUPLICADA"
    finally:
        app.dependency_overrides.clear()


def test_criar_metrica_422_fora_da_janela(client: TestClient) -> None:
    user = _cliente()
    uc = _mock_uc(execute_raises=MetricaForaDaJanela("janela"))
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_criar_metrica] = lambda: uc
    try:
        r = client.post(
            "/api/v1/metricas",
            json={
                "semana_inicio": "2026-01-05",
                "ligacoes_agendadas": 0,
                "ligacoes_realizadas": 0,
                "reunioes_agendadas": 0,
                "indicacoes": 0,
            },
        )
        assert r.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_criar_metrica_422_semana_futura(client: TestClient) -> None:
    user = _cliente()
    uc = _mock_uc(execute_raises=SemanaFuturaNaoPermitida("futura"))
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_criar_metrica] = lambda: uc
    try:
        r = client.post(
            "/api/v1/metricas",
            json={
                "semana_inicio": "2026-06-01",
                "ligacoes_agendadas": 0,
                "ligacoes_realizadas": 0,
                "reunioes_agendadas": 0,
                "indicacoes": 0,
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
                "usuario_id": str(uuid4()),  # different user
                "semana_inicio": "2026-05-11",
                "ligacoes_agendadas": 0,
                "ligacoes_realizadas": 0,
                "reunioes_agendadas": 0,
                "indicacoes": 0,
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
    app.dependency_overrides[get_atualizar_metrica] = lambda: uc
    try:
        r = client.patch(f"/api/v1/metricas/{uuid4()}", json={"ligacoes_agendadas": 20})
        assert r.status_code == 200
    finally:
        app.dependency_overrides.clear()


def test_atualizar_metrica_404(client: TestClient) -> None:
    user = _cliente()
    uc = _mock_uc(execute_raises=MetricaNaoEncontrada("nope"))
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_atualizar_metrica] = lambda: uc
    try:
        r = client.patch(f"/api/v1/metricas/{uuid4()}", json={"ligacoes_agendadas": 5})
        assert r.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_atualizar_metrica_403_wrong_owner(client: TestClient) -> None:
    user = _cliente()
    uc = _mock_uc(execute_raises=MetricaNaoPertenceAoUsuario("not yours"))
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_atualizar_metrica] = lambda: uc
    try:
        r = client.patch(f"/api/v1/metricas/{uuid4()}", json={"ligacoes_agendadas": 5})
        assert r.status_code == 403
    finally:
        app.dependency_overrides.clear()


# ── GET /dashboard/resumo ──────────────────────────────────────────────────────

def test_obter_resumo_200(client: TestClient) -> None:
    user = _cliente()
    dto = ResumoDashboardDTO(
        mes="2026-05",
        ligacoes_agendadas=DeltaDTO(valor=120, delta_pct=20.0),
        ligacoes_realizadas=DeltaDTO(valor=95, delta_pct=None),
        reunioes_agendadas=DeltaDTO(valor=28, delta_pct=40.0),
        indicacoes=DeltaDTO(valor=12, delta_pct=None),
    )
    uc = _mock_uc(execute_return=dto)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_resumo_dashboard] = lambda: uc
    try:
        r = client.get("/api/v1/dashboard/resumo")
        assert r.status_code == 200
        body = r.json()
        assert body["mes"] == "2026-05"
        assert body["ligacoes_realizadas"]["delta_pct"] is None
    finally:
        app.dependency_overrides.clear()


def test_obter_resumo_requires_auth(client: TestClient) -> None:
    r = client.get("/api/v1/dashboard/resumo")
    assert r.status_code == 401


# ── GET /dashboard/series ──────────────────────────────────────────────────────

def test_obter_series_200(client: TestClient) -> None:
    user = _cliente()
    dto = SeriesDashboardDTO(
        series=[
            SerieSemanalDTO(
                semana=date(2026, 5, 11),
                ligacoes_agendadas=10,
                ligacoes_realizadas=8,
                reunioes_agendadas=3,
                indicacoes=1,
            )
        ]
    )
    uc = _mock_uc(execute_return=dto)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_series_dashboard] = lambda: uc
    try:
        r = client.get("/api/v1/dashboard/series?semanas=1")
        assert r.status_code == 200
        assert len(r.json()["series"]) == 1
    finally:
        app.dependency_overrides.clear()


# ── GET /admin/dashboard ───────────────────────────────────────────────────────

def test_admin_dashboard_200(client: TestClient) -> None:
    admin = _admin()
    dto = AdminConsolidadoDTO(
        agregados=AgregadosAdminDTO(
            ligacoes_agendadas_total=100,
            ligacoes_realizadas_total=80,
            reunioes_agendadas_total=20,
            indicacoes_total=5,
            mentorados_com_metrica_no_mes=3,
            mentorados_sem_metrica_no_mes=2,
        ),
        items=[
            UsuarioMetricasMesDTO(
                usuario_id=uuid4(),
                nome="Alice",
                foto_url=None,
                ligacoes_agendadas=100,
                ligacoes_realizadas=80,
                reunioes_agendadas=20,
                indicacoes=5,
                ultima_metrica_em=date(2026, 5, 4),
            )
        ],
        page=1,
        page_size=20,
        total=1,
    )
    uc = _mock_uc(execute_return=dto)
    app.dependency_overrides[get_current_user] = lambda: admin
    app.dependency_overrides[require_admin] = lambda: admin
    app.dependency_overrides[get_admin_consolidado] = lambda: uc
    try:
        r = client.get("/api/v1/admin/dashboard")
        assert r.status_code == 200
        body = r.json()
        assert body["agregados"]["mentorados_com_metrica_no_mes"] == 3
        assert body["items"][0]["nome"] == "Alice"
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
