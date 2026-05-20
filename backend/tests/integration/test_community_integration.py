"""Integration tests: comunidade router → real ListarComunidade use case → fake repo.

Verifies:
- telefone never appears in any response item
- Admins are excluded (only clientes returned by listar_ativos)
- Pagination params are forwarded correctly
- Response shape matches spec
"""

import json
from typing import Any
from uuid import UUID, uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.contexts.auth.domain.entities import User as AuthUser
from app.contexts.community.domain.entities import CommunityMember
from app.contexts.community.infrastructure.repositories import SqlAlchemyCommunityRepository
from app.contexts.community.presentation.router import _get_listar_comunidade, router
from app.core.deps import get_current_user
from app.core.exceptions import AppException

_app = FastAPI()
_app.include_router(router, prefix="/api/v1")


@_app.exception_handler(AppException)
async def _exc(request: Request, exc: AppException) -> JSONResponse:
    body: dict[str, Any] = {"error": {"code": exc.code, "message": exc.message}}
    return JSONResponse(status_code=exc.status, content=body)


_AUTH_USER = AuthUser(id=uuid4(), email="user@test.com", role="cliente", inativo=False)


class _FakeRepo:
    """Simulates repository that already filters: only clientes, not inativo."""

    def __init__(self, membros: list[CommunityMember], total: int) -> None:
        self._membros = membros
        self._total = total
        self.last_page: int | None = None
        self.last_page_size: int | None = None

    async def list_active(self, page: int, page_size: int) -> tuple[list[CommunityMember], int]:
        self.last_page = page
        self.last_page_size = page_size
        offset = (page - 1) * page_size
        return self._membros[offset : offset + page_size], self._total


def _make_membro(
    nome: str,
    *,
    foto_url: str | None = None,
    linkedin_url: str | None = None,
    instagram_username: str | None = None,
    uid: UUID | None = None,
) -> CommunityMember:
    return CommunityMember(
        id=uid or uuid4(),
        nome=nome,
        foto_url=foto_url,
        linkedin_url=linkedin_url,
        instagram_username=instagram_username,
    )


def _client(repo: _FakeRepo) -> TestClient:
    from app.contexts.community.application.use_cases.list_community import ListarComunidade

    _app.dependency_overrides[get_current_user] = lambda: _AUTH_USER
    _app.dependency_overrides[_get_listar_comunidade] = lambda: ListarComunidade(repo=repo)
    return TestClient(_app, raise_server_exceptions=False)


def _clear() -> None:
    _app.dependency_overrides.clear()


# ── Response shape ────────────────────────────────────────────────────────────


def test_response_has_correct_shape() -> None:
    membro = _make_membro("Ana", foto_url="https://cdn.x/ana.jpg")
    repo = _FakeRepo([membro], total=1)
    client = _client(repo)
    try:
        resp = client.get("/api/v1/comunidade")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "page" in data
        assert "page_size" in data
        assert "total" in data
        assert data["total"] == 1
        assert data["page"] == 1
        assert len(data["items"]) == 1
    finally:
        _clear()


# ── Telefone never in response ────────────────────────────────────────────────


def test_telefone_never_in_response_single_item() -> None:
    membro = _make_membro("Ana")
    repo = _FakeRepo([membro], total=1)
    client = _client(repo)
    try:
        resp = client.get("/api/v1/comunidade")
        raw = resp.text
        assert "telefone" not in raw
        for item in resp.json()["items"]:
            assert "telefone" not in item
    finally:
        _clear()


def test_telefone_never_in_response_multiple_items() -> None:
    membros = [_make_membro(n) for n in ["Ana", "Bia", "Carlos"]]
    repo = _FakeRepo(membros, total=3)
    client = _client(repo)
    try:
        resp = client.get("/api/v1/comunidade")
        # grep-style check on the raw JSON text
        assert "telefone" not in resp.text
        for item in resp.json()["items"]:
            assert "telefone" not in item
    finally:
        _clear()


def test_telefone_never_in_empty_response() -> None:
    repo = _FakeRepo([], total=0)
    client = _client(repo)
    try:
        resp = client.get("/api/v1/comunidade")
        assert resp.status_code == 200
        assert "telefone" not in resp.text
    finally:
        _clear()


# ── Admins excluded ───────────────────────────────────────────────────────────


def test_repo_sql_filter_excludes_admins() -> None:
    """Verify the SQL query in the repository filters role='cliente' and inativo=false."""
    import inspect

    source = inspect.getsource(SqlAlchemyCommunityRepository.listar_ativos)
    assert "role = 'cliente'" in source
    assert "inativo = false" in source


def test_only_clientes_returned_by_list_active() -> None:
    """Fake repo contract: listar_ativos must only return clientes (not admins)."""
    # listar_ativos is supposed to return pre-filtered clientes only.
    # We test that whatever listar_ativos returns ends up in the response without mutation.
    cliente1 = _make_membro("Cliente Ana")
    cliente2 = _make_membro("Cliente Bia")
    repo = _FakeRepo([cliente1, cliente2], total=2)
    client = _client(repo)
    try:
        resp = client.get("/api/v1/comunidade")
        assert resp.status_code == 200
        nomes = [item["nome"] for item in resp.json()["items"]]
        assert "Cliente Ana" in nomes
        assert "Cliente Bia" in nomes
        assert len(nomes) == 2
    finally:
        _clear()


# ── Pagination ────────────────────────────────────────────────────────────────


def test_default_pagination_params() -> None:
    repo = _FakeRepo([], total=0)
    client = _client(repo)
    try:
        client.get("/api/v1/comunidade")
        assert repo.last_page == 1
        assert repo.last_page_size == 24
    finally:
        _clear()


def test_custom_pagination_params_forwarded() -> None:
    membros = [_make_membro(f"User {i}") for i in range(50)]
    repo = _FakeRepo(membros, total=50)
    client = _client(repo)
    try:
        resp = client.get("/api/v1/comunidade?page=2&page_size=10")
        assert resp.status_code == 200
        data = resp.json()
        assert data["page"] == 2
        assert data["page_size"] == 10
        assert repo.last_page == 2
        assert repo.last_page_size == 10
    finally:
        _clear()


def test_page_size_0_rejected() -> None:
    repo = _FakeRepo([], total=0)
    client = _client(repo)
    try:
        resp = client.get("/api/v1/comunidade?page_size=0")
        assert resp.status_code in (400, 422)
    finally:
        _clear()


def test_page_0_rejected() -> None:
    repo = _FakeRepo([], total=0)
    client = _client(repo)
    try:
        resp = client.get("/api/v1/comunidade?page=0")
        assert resp.status_code in (400, 422)
    finally:
        _clear()


# ── Item fields ────────────────────────────────────────────────────────────────


def test_item_contains_expected_fields() -> None:
    uid = uuid4()
    membro = _make_membro(
        "Carlos",
        foto_url="https://cdn.x/carlos.jpg",
        linkedin_url="https://linkedin.com/in/carlos",
        instagram_username="carlos.ig",
        uid=uid,
    )
    repo = _FakeRepo([membro], total=1)
    client = _client(repo)
    try:
        resp = client.get("/api/v1/comunidade")
        item = resp.json()["items"][0]
        assert item["id"] == str(uid)
        assert item["nome"] == "Carlos"
        assert item["foto_url"] == "https://cdn.x/carlos.jpg"
        assert item["linkedin_url"] == "https://linkedin.com/in/carlos"
        assert item["instagram_username"] == "carlos.ig"
    finally:
        _clear()


def test_optional_fields_can_be_null() -> None:
    membro = _make_membro("Maria")
    repo = _FakeRepo([membro], total=1)
    client = _client(repo)
    try:
        resp = client.get("/api/v1/comunidade")
        item = resp.json()["items"][0]
        assert item["foto_url"] is None
        assert item["linkedin_url"] is None
        assert item["instagram_username"] is None
    finally:
        _clear()


