"""HTTP-layer tests using FastAPI TestClient with dependency overrides."""
from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.contexts.auth.domain.entities import Usuario
from app.contexts.conteudo.application.dtos import (
    AulaDetalheDTO,
    AulaResumoDTO,
    ComentarioDTO,
    AutorDTO,
    ModuloComAulasDTO,
    TrilhaComModulosDTO,
    TrilhaProgressoDTO,
    TrilhaResumoDTO,
)
from app.contexts.conteudo.domain.entities import Aula, Comentario, Modulo, Trilha
from app.contexts.conteudo.domain.exceptions import (
    AulaNaoEncontrada,
    ComentarioNaoEncontrado,
    ComentarioNaoPertenceAoUsuario,
    DriveUrlInvalida,
    ModuloNaoEncontrado,
    TrilhaNaoEncontrada,
)
from app.contexts.conteudo.presentation.deps import (
    get_apagar_comentario,
    get_atualizar_aula,
    get_atualizar_modulo,
    get_atualizar_trilha,
    get_criar_aula,
    get_criar_comentario,
    get_criar_modulo,
    get_criar_trilha,
    get_desmarcar_concluida,
    get_editar_comentario,
    get_listar_comentarios,
    get_listar_trilhas,
    get_marcar_concluida,
    get_obter_aula,
    get_obter_trilha,
    get_remover_aula,
    get_remover_modulo,
    get_remover_trilha,
    get_reordenar_aulas,
    get_reordenar_modulos,
    get_reordenar_trilhas,
)
from app.core.deps import get_current_user, require_admin
from app.main import app
from app.shared.application.dtos import PagedResponse


# ── Auth helpers ───────────────────────────────────────────────────────────────

def _cliente(user_id: UUID | None = None) -> Usuario:
    return Usuario(id=user_id or uuid4(), email="user@test.com", role="cliente", inativo=False)


def _admin(user_id: UUID | None = None) -> Usuario:
    return Usuario(id=user_id or uuid4(), email="admin@test.com", role="admin", inativo=False)


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


def _base_trilha(trilha_id: UUID | None = None) -> Trilha:
    return Trilha(
        id=trilha_id or uuid4(), titulo="T", descricao=None, capa_url=None,
        ordem=0, criado_em=datetime.now(tz=UTC)
    )


def _base_aula(aula_id: UUID | None = None, modulo_id: UUID | None = None) -> Aula:
    return Aula(
        id=aula_id or uuid4(), modulo_id=modulo_id or uuid4(), titulo="A",
        descricao=None, drive_file_id="abc", duracao_minutos=None,
        ordem=0, criado_em=datetime.now(tz=UTC)
    )


def _base_modulo(modulo_id: UUID | None = None, trilha_id: UUID | None = None) -> Modulo:
    return Modulo(
        id=modulo_id or uuid4(), trilha_id=trilha_id or uuid4(),
        titulo="M", descricao=None, ordem=0
    )


# ── GET /trilhas ───────────────────────────────────────────────────────────────

def test_listar_trilhas_returns_200(client: TestClient) -> None:
    user = _cliente()
    trilha_id = uuid4()
    dto = TrilhaProgressoDTO(
        id=trilha_id, titulo="T", descricao=None, capa_url=None,
        total_aulas=5, aulas_concluidas=2, progresso_pct=40.0
    )
    uc = _mock_uc(execute_return=[dto])
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_listar_trilhas] = lambda: uc
    try:
        r = client.get("/api/v1/trilhas")
        assert r.status_code == 200
        assert r.json()[0]["progresso_pct"] == 40.0
    finally:
        app.dependency_overrides.clear()


def test_listar_trilhas_requires_auth(client: TestClient) -> None:
    r = client.get("/api/v1/trilhas")
    assert r.status_code == 401


# ── GET /trilhas/{id} ──────────────────────────────────────────────────────────

def test_obter_trilha_returns_200(client: TestClient) -> None:
    user = _cliente()
    trilha_id = uuid4()
    dto = TrilhaComModulosDTO(
        id=trilha_id, titulo="T", descricao=None, capa_url=None,
        progresso_pct=0.0,
        modulos=[
            ModuloComAulasDTO(id=uuid4(), titulo="M", descricao=None, ordem=0, aulas=[])
        ],
    )
    uc = _mock_uc(execute_return=dto)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_obter_trilha] = lambda: uc
    try:
        r = client.get(f"/api/v1/trilhas/{trilha_id}")
        assert r.status_code == 200
        assert r.json()["id"] == str(trilha_id)
    finally:
        app.dependency_overrides.clear()


def test_obter_trilha_404(client: TestClient) -> None:
    user = _cliente()
    uc = _mock_uc(execute_raises=TrilhaNaoEncontrada("not found"))
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_obter_trilha] = lambda: uc
    try:
        r = client.get(f"/api/v1/trilhas/{uuid4()}")
        assert r.status_code == 404
    finally:
        app.dependency_overrides.clear()


# ── GET /aulas/{id} ────────────────────────────────────────────────────────────

def test_obter_aula_returns_200(client: TestClient) -> None:
    user = _cliente()
    aula_id = uuid4()
    dto = AulaDetalheDTO(
        id=aula_id, modulo_id=uuid4(), titulo="A", descricao=None,
        drive_file_id="abc", duracao_minutos=None, concluida=False,
        trilha=TrilhaResumoDTO(id=uuid4(), titulo="T"),
        proxima_aula=None,
    )
    uc = _mock_uc(execute_return=dto)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_obter_aula] = lambda: uc
    try:
        r = client.get(f"/api/v1/aulas/{aula_id}")
        assert r.status_code == 200
        assert r.json()["proxima_aula"] is None
    finally:
        app.dependency_overrides.clear()


def test_obter_aula_404(client: TestClient) -> None:
    user = _cliente()
    uc = _mock_uc(execute_raises=AulaNaoEncontrada("nope"))
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_obter_aula] = lambda: uc
    try:
        r = client.get(f"/api/v1/aulas/{uuid4()}")
        assert r.status_code == 404
    finally:
        app.dependency_overrides.clear()


# ── POST /aulas/{id}/concluir ──────────────────────────────────────────────────

def test_marcar_concluida_204(client: TestClient) -> None:
    user = _cliente()
    uc = _mock_uc(execute_return=None)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_marcar_concluida] = lambda: uc
    try:
        r = client.post(f"/api/v1/aulas/{uuid4()}/concluir")
        assert r.status_code == 204
    finally:
        app.dependency_overrides.clear()


def test_desmarcar_concluida_204(client: TestClient) -> None:
    user = _cliente()
    uc = _mock_uc(execute_return=None)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_desmarcar_concluida] = lambda: uc
    try:
        r = client.delete(f"/api/v1/aulas/{uuid4()}/concluir")
        assert r.status_code == 204
    finally:
        app.dependency_overrides.clear()


# ── Admin trilhas ──────────────────────────────────────────────────────────────

def test_admin_criar_trilha_201(client: TestClient) -> None:
    user = _admin()
    trilha = _base_trilha()
    uc = _mock_uc(execute_return=trilha)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[require_admin] = lambda: user
    app.dependency_overrides[get_criar_trilha] = lambda: uc
    try:
        r = client.post("/api/v1/admin/trilhas", json={"titulo": "T"})
        assert r.status_code == 201
    finally:
        app.dependency_overrides.clear()


def test_admin_criar_trilha_requires_admin(client: TestClient) -> None:
    user = _cliente()
    app.dependency_overrides[get_current_user] = lambda: user
    try:
        r = client.post("/api/v1/admin/trilhas", json={"titulo": "T"})
        assert r.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_admin_remover_trilha_404(client: TestClient) -> None:
    user = _admin()
    uc = _mock_uc(execute_raises=TrilhaNaoEncontrada("nope"))
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[require_admin] = lambda: user
    app.dependency_overrides[get_remover_trilha] = lambda: uc
    try:
        r = client.delete(f"/api/v1/admin/trilhas/{uuid4()}")
        assert r.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_admin_reordenar_trilhas_204(client: TestClient) -> None:
    user = _admin()
    uc = _mock_uc(execute_return=None)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[require_admin] = lambda: user
    app.dependency_overrides[get_reordenar_trilhas] = lambda: uc
    try:
        r = client.post(
            "/api/v1/admin/trilhas/reordenar",
            json={"ordem": [{"id": str(uuid4()), "ordem": 0}]},
        )
        assert r.status_code == 204
    finally:
        app.dependency_overrides.clear()


# ── Admin modulos ──────────────────────────────────────────────────────────────

def test_admin_criar_modulo_201(client: TestClient) -> None:
    user = _admin()
    modulo = _base_modulo()
    uc = _mock_uc(execute_return=modulo)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[require_admin] = lambda: user
    app.dependency_overrides[get_criar_modulo] = lambda: uc
    try:
        r = client.post(
            "/api/v1/admin/modulos",
            json={"trilha_id": str(uuid4()), "titulo": "M"},
        )
        assert r.status_code == 201
    finally:
        app.dependency_overrides.clear()


def test_admin_remover_modulo_404(client: TestClient) -> None:
    user = _admin()
    uc = _mock_uc(execute_raises=ModuloNaoEncontrado("nope"))
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[require_admin] = lambda: user
    app.dependency_overrides[get_remover_modulo] = lambda: uc
    try:
        r = client.delete(f"/api/v1/admin/modulos/{uuid4()}")
        assert r.status_code == 404
    finally:
        app.dependency_overrides.clear()


# ── Admin aulas ────────────────────────────────────────────────────────────────

def test_admin_criar_aula_invalid_drive_url_400(client: TestClient) -> None:
    user = _admin()
    uc = _mock_uc(execute_raises=DriveUrlInvalida("bad-url"))
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[require_admin] = lambda: user
    app.dependency_overrides[get_criar_aula] = lambda: uc
    try:
        r = client.post(
            "/api/v1/admin/aulas",
            json={
                "modulo_id": str(uuid4()),
                "titulo": "A",
                "drive_url": "bad",
            },
        )
        assert r.status_code == 400
        assert r.json()["error"]["code"] == "DRIVE_URL_INVALID"
    finally:
        app.dependency_overrides.clear()


def test_admin_criar_aula_201(client: TestClient) -> None:
    user = _admin()
    aula = _base_aula()
    uc = _mock_uc(execute_return=aula)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[require_admin] = lambda: user
    app.dependency_overrides[get_criar_aula] = lambda: uc
    try:
        r = client.post(
            "/api/v1/admin/aulas",
            json={
                "modulo_id": str(uuid4()),
                "titulo": "Aula",
                "drive_url": "https://drive.google.com/file/d/abc/view",
            },
        )
        assert r.status_code == 201
    finally:
        app.dependency_overrides.clear()


def test_admin_reordenar_aulas_204(client: TestClient) -> None:
    user = _admin()
    uc = _mock_uc(execute_return=None)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[require_admin] = lambda: user
    app.dependency_overrides[get_reordenar_aulas] = lambda: uc
    try:
        r = client.post(
            "/api/v1/admin/aulas/reordenar",
            json={"ordem": [{"id": str(uuid4()), "ordem": 0}]},
        )
        assert r.status_code == 204
    finally:
        app.dependency_overrides.clear()


# ── Comentarios ────────────────────────────────────────────────────────────────

def test_listar_comentarios_200(client: TestClient) -> None:
    user = _cliente()
    now = datetime.now(tz=UTC)
    paged: PagedResponse[ComentarioDTO] = PagedResponse(
        items=[
            ComentarioDTO(
                id=uuid4(),
                autor=AutorDTO(id=uuid4(), nome="Alice", foto_url=None),
                texto="Ótimo!",
                criado_em=now,
                editado_em=None,
                apagado_em=None,
                is_proprio=False,
            )
        ],
        page=1,
        page_size=20,
        total=1,
    )
    uc = _mock_uc(execute_return=paged)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_listar_comentarios] = lambda: uc
    try:
        r = client.get(f"/api/v1/aulas/{uuid4()}/comentarios")
        assert r.status_code == 200
        assert r.json()["total"] == 1
    finally:
        app.dependency_overrides.clear()


def test_criar_comentario_texto_muito_longo_400(client: TestClient) -> None:
    user = _cliente()
    app.dependency_overrides[get_current_user] = lambda: user
    try:
        r = client.post(
            f"/api/v1/aulas/{uuid4()}/comentarios",
            json={"texto": "x" * 2001},
        )
        assert r.status_code == 400
    finally:
        app.dependency_overrides.clear()


def test_editar_comentario_403(client: TestClient) -> None:
    user = _cliente()
    uc = _mock_uc(execute_raises=ComentarioNaoPertenceAoUsuario("sem permissão"))
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_editar_comentario] = lambda: uc
    try:
        r = client.patch(f"/api/v1/comentarios/{uuid4()}", json={"texto": "hack"})
        assert r.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_apagar_comentario_404(client: TestClient) -> None:
    user = _cliente()
    uc = _mock_uc(execute_raises=ComentarioNaoEncontrado("nope"))
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_apagar_comentario] = lambda: uc
    try:
        r = client.delete(f"/api/v1/comentarios/{uuid4()}")
        assert r.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_apagar_comentario_204(client: TestClient) -> None:
    user = _cliente()
    uc = _mock_uc(execute_return=None)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_apagar_comentario] = lambda: uc
    try:
        r = client.delete(f"/api/v1/comentarios/{uuid4()}")
        assert r.status_code == 204
    finally:
        app.dependency_overrides.clear()


def test_admin_atualizar_trilha_404(client: TestClient) -> None:
    user = _admin()
    uc = _mock_uc(execute_raises=TrilhaNaoEncontrada("nope"))
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[require_admin] = lambda: user
    app.dependency_overrides[get_atualizar_trilha] = lambda: uc
    try:
        r = client.patch(f"/api/v1/admin/trilhas/{uuid4()}", json={"titulo": "X"})
        assert r.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_admin_atualizar_modulo_404(client: TestClient) -> None:
    user = _admin()
    uc = _mock_uc(execute_raises=ModuloNaoEncontrado("nope"))
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[require_admin] = lambda: user
    app.dependency_overrides[get_atualizar_modulo] = lambda: uc
    try:
        r = client.patch(f"/api/v1/admin/modulos/{uuid4()}", json={"titulo": "X"})
        assert r.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_admin_reordenar_modulos_204(client: TestClient) -> None:
    user = _admin()
    uc = _mock_uc(execute_return=None)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[require_admin] = lambda: user
    app.dependency_overrides[get_reordenar_modulos] = lambda: uc
    try:
        r = client.post(
            "/api/v1/admin/modulos/reordenar",
            json={"ordem": [{"id": str(uuid4()), "ordem": 0}]},
        )
        assert r.status_code == 204
    finally:
        app.dependency_overrides.clear()
