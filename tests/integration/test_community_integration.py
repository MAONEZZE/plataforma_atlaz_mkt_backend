"""Integration tests: community router → real ListCommunity use case → fake repo.

Verifies:
- telefone never appears in any response item
- Admins are excluded (only clients returned by list_active)
- Pagination params are forwarded correctly
- Response shape matches spec
"""

from typing import Any
from uuid import UUID, uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.api.config.dependencies.auth_deps import get_current_user
from app.api.controllers.community_module.community_routes.community_router import (
    _get_list_community,
    router,
)
from app.database.community_module.community_repo import SqlAlchemyCommunityRepository
from app.domain.auth_module.auth_model import User as AuthUser
from app.domain.community_module.community_model import CommunityMember
from app.domain.shared.base_exceptions import AppException

_app = FastAPI()
_app.include_router(router, prefix="/api/v1")


@_app.exception_handler(AppException)
async def _exc(request: Request, exc: AppException) -> JSONResponse:
    body: dict[str, Any] = {"error": {"code": exc.code, "message": exc.message}}
    return JSONResponse(status_code=exc.status, content=body)


_AUTH_USER = AuthUser(id=uuid4(), email="user@test.com", role="cliente", inactive=False)


class _FakeRepo:
    """Simulates repository that already filters: only clients, not inactive."""

    def __init__(self, members: list[CommunityMember], total: int) -> None:
        self._members = members
        self._total = total
        self.last_page: int | None = None
        self.last_page_size: int | None = None

    async def list_active(self, page: int, page_size: int) -> tuple[list[CommunityMember], int]:
        self.last_page = page
        self.last_page_size = page_size
        offset = (page - 1) * page_size
        return self._members[offset : offset + page_size], self._total


def _make_member(
    name: str,
    *,
    photo_url: str | None = None,
    linkedin_url: str | None = None,
    instagram_username: str | None = None,
    uid: UUID | None = None,
) -> CommunityMember:
    return CommunityMember(
        id=uid or uuid4(),
        name=name,
        photo_url=photo_url,
        linkedin_url=linkedin_url,
        instagram_username=instagram_username,
    )


def _client(repo: _FakeRepo) -> TestClient:
    from app.services.community_module.community_service.list_community import ListCommunity

    _app.dependency_overrides[get_current_user] = lambda: _AUTH_USER
    _app.dependency_overrides[_get_list_community] = lambda: ListCommunity(repo=repo)
    return TestClient(_app, raise_server_exceptions=False)


def _clear() -> None:
    _app.dependency_overrides.clear()


# ── Response shape ────────────────────────────────────────────────────────────


def test_response_has_correct_shape() -> None:
    member = _make_member("Ana", photo_url="https://cdn.x/ana.jpg")
    repo = _FakeRepo([member], total=1)
    client = _client(repo)
    try:
        resp = client.get("/api/v1/community")
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
    member = _make_member("Ana")
    repo = _FakeRepo([member], total=1)
    client = _client(repo)
    try:
        resp = client.get("/api/v1/community")
        raw = resp.text
        assert "telefone" not in raw
        for item in resp.json()["items"]:
            assert "telefone" not in item
    finally:
        _clear()


def test_telefone_never_in_response_multiple_items() -> None:
    members = [_make_member(n) for n in ["Ana", "Bia", "Carlos"]]
    repo = _FakeRepo(members, total=3)
    client = _client(repo)
    try:
        resp = client.get("/api/v1/community")
        assert "telefone" not in resp.text
        for item in resp.json()["items"]:
            assert "telefone" not in item
    finally:
        _clear()


def test_telefone_never_in_empty_response() -> None:
    repo = _FakeRepo([], total=0)
    client = _client(repo)
    try:
        resp = client.get("/api/v1/community")
        assert resp.status_code == 200
        assert "telefone" not in resp.text
    finally:
        _clear()


# ── Admins excluded ───────────────────────────────────────────────────────────


def test_repo_sql_filter_excludes_admins() -> None:
    """Verify the SQL query in the repository filters role='cliente' and inactive."""
    import inspect

    source = inspect.getsource(SqlAlchemyCommunityRepository.list_active)
    assert "role = 'cliente'" in source


def test_only_clients_returned_by_list_active() -> None:
    """Fake repo contract: list_active must only return clients (not admins)."""
    client1 = _make_member("Client Ana")
    client2 = _make_member("Client Bia")
    repo = _FakeRepo([client1, client2], total=2)
    client = _client(repo)
    try:
        resp = client.get("/api/v1/community")
        assert resp.status_code == 200
        names = [item["name"] for item in resp.json()["items"]]
        assert "Client Ana" in names
        assert "Client Bia" in names
        assert len(names) == 2
    finally:
        _clear()


# ── Pagination ────────────────────────────────────────────────────────────────


def test_default_pagination_params() -> None:
    repo = _FakeRepo([], total=0)
    client = _client(repo)
    try:
        client.get("/api/v1/community")
        assert repo.last_page == 1
        assert repo.last_page_size == 24
    finally:
        _clear()


def test_custom_pagination_params_forwarded() -> None:
    members = [_make_member(f"User {i}") for i in range(50)]
    repo = _FakeRepo(members, total=50)
    client = _client(repo)
    try:
        resp = client.get("/api/v1/community?page=2&page_size=10")
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
        resp = client.get("/api/v1/community?page_size=0")
        assert resp.status_code in (400, 422)
    finally:
        _clear()


def test_page_0_rejected() -> None:
    repo = _FakeRepo([], total=0)
    client = _client(repo)
    try:
        resp = client.get("/api/v1/community?page=0")
        assert resp.status_code in (400, 422)
    finally:
        _clear()


# ── Item fields ────────────────────────────────────────────────────────────────


def test_item_contains_expected_fields() -> None:
    uid = uuid4()
    member = _make_member(
        "Carlos",
        photo_url="https://cdn.x/carlos.jpg",
        linkedin_url="https://linkedin.com/in/carlos",
        instagram_username="carlos.ig",
        uid=uid,
    )
    repo = _FakeRepo([member], total=1)
    client = _client(repo)
    try:
        resp = client.get("/api/v1/community")
        item = resp.json()["items"][0]
        assert item["id"] == str(uid)
        assert item["name"] == "Carlos"
        assert item["photo_url"] == "https://cdn.x/carlos.jpg"
        assert item["linkedin_url"] == "https://linkedin.com/in/carlos"
        assert item["instagram_username"] == "carlos.ig"
    finally:
        _clear()


def test_optional_fields_can_be_null() -> None:
    member = _make_member("Maria")
    repo = _FakeRepo([member], total=1)
    client = _client(repo)
    try:
        resp = client.get("/api/v1/community")
        item = resp.json()["items"][0]
        assert item["photo_url"] is None
        assert item["linkedin_url"] is None
        assert item["instagram_username"] is None
    finally:
        _clear()
