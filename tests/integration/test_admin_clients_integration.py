"""Integration tests: admin router → real CreateClient use case → fake repo + fake gateway.

Service trusts the Supabase trigger (atomic with auth.users INSERT) and
constructs the User entity from input — no DB read after create. These
tests reflect that contract.
"""

from typing import Any
from uuid import UUID, uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.api.config.dependencies.auth_deps import get_current_user, require_admin
from app.api.controllers.user_module.user_routes.admin_router import (
    _create_client,
    _list_clients,
    admin_router,
)
from app.domain.auth_module.auth_model import User as AuthUser
from app.domain.shared.base_exceptions import AppException
from app.domain.shared.utils import now_sp
from app.domain.user_module.user_exceptions import EmailAlreadyRegistered
from app.domain.user_module.user_model import User
from app.services.user_module.create_client_service import CreateClient
from app.services.user_module.list_clients_service import ListClients

_app = FastAPI()
_app.include_router(admin_router, prefix="/api/v1")


@_app.exception_handler(AppException)
async def _exc(request: Request, exc: AppException) -> JSONResponse:
    body: dict[str, Any] = {"error": {"code": exc.code, "message": exc.message}}
    return JSONResponse(status_code=exc.status, content=body)


def _admin_user() -> AuthUser:
    return AuthUser(id=uuid4(), email="admin@test.com", role="admin", inactive=False)


class _FakeGateway:
    def __init__(self, user_id: UUID, exc: Exception | None = None) -> None:
        self._user_id = user_id
        self._exc = exc
        self.last_kwargs: dict[str, Any] | None = None

    def create_user(self, email: str, password: str, name: str, role: str) -> UUID:
        self.last_kwargs = {"email": email, "password": password, "name": name, "role": role}
        if self._exc is not None:
            raise self._exc
        return self._user_id


class _FakeRepo:
    def __init__(
        self,
        update_raises: Exception | None = None,
        upsert_raises: Exception | None = None,
        list_result: tuple[list[User], int] | None = None,
    ) -> None:
        self._update_raises = update_raises
        self._upsert_raises = upsert_raises
        self._list_result = list_result or ([], 0)
        self.upsert_called_with: User | None = None
        self.list_called_with: tuple[int, int] | None = None

    async def get_by_id(self, user_id: UUID) -> User | None:
        raise AssertionError("service must not call get_by_id")

    async def upsert_new(self, user: User) -> None:
        self.upsert_called_with = user
        if self._upsert_raises is not None:
            raise self._upsert_raises

    async def update(self, user: User) -> User:
        if self._update_raises is not None:
            raise self._update_raises
        return user

    async def list_clients(
        self, page: int, page_size: int
    ) -> tuple[list[User], int]:
        self.list_called_with = (page, page_size)
        return self._list_result


def _use_case(repo: _FakeRepo, gateway: _FakeGateway) -> CreateClient:
    return CreateClient(repo=repo, gateway=gateway)  # type: ignore[arg-type]


def _list_use_case(repo: _FakeRepo) -> ListClients:
    return ListClients(repo=repo)  # type: ignore[arg-type]


def _make_client(name: str = "Maria", phone: str | None = "+5511999999999") -> User:
    now = now_sp()
    return User(
        id=uuid4(),
        name=name,
        email=f"{name.lower()}@test.com",
        phone=phone,
        linkedin_url=None,
        instagram_username=None,
        description=None,
        photo_url=None,
        role="cliente",
        inactive=False,
        created_at=now,
        updated_at=now,
    )


def _client(
    use_case: CreateClient | None = None,
    *,
    admin: bool = True,
    list_uc: ListClients | None = None,
) -> TestClient:
    if admin:
        _app.dependency_overrides[require_admin] = lambda: _admin_user()
        _app.dependency_overrides[get_current_user] = lambda: _admin_user()
    else:
        non_admin = AuthUser(id=uuid4(), email="user@test.com", role="cliente", inactive=False)
        _app.dependency_overrides[get_current_user] = lambda: non_admin
        _app.dependency_overrides.pop(require_admin, None)
    if use_case is not None:
        _app.dependency_overrides[_create_client] = lambda: use_case
    if list_uc is not None:
        _app.dependency_overrides[_list_clients] = lambda: list_uc
    return TestClient(_app, raise_server_exceptions=False)


def _clear() -> None:
    _app.dependency_overrides.clear()


# ── 201 happy path ────────────────────────────────────────────────────────────


def test_create_client_returns_201_and_user_response_shape() -> None:
    uid = uuid4()
    gateway = _FakeGateway(uid)
    repo = _FakeRepo()
    client = _client(_use_case(repo, gateway))
    try:
        resp = client.post(
            "/api/v1/admin/clients",
            json={
                "name": "Maria",
                "email": "maria@test.com",
                "password": "Senha@123",
                "phone": "+5511999999999",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["id"] == str(uid)
        assert data["name"] == "Maria"
        assert data["email"] == "maria@test.com"
        assert data["phone"] == "+5511999999999"
        assert data["role"] == "cliente"
        assert "created_at" in data
        assert "password" not in resp.text
        assert gateway.last_kwargs is not None
        assert gateway.last_kwargs["role"] == "cliente"
    finally:
        _clear()


def test_create_client_without_phone_returns_201() -> None:
    uid = uuid4()
    gateway = _FakeGateway(uid)
    repo = _FakeRepo()
    client = _client(_use_case(repo, gateway))
    try:
        resp = client.post(
            "/api/v1/admin/clients",
            json={"name": "Maria", "email": "maria@test.com", "password": "Senha@123"},
        )
        assert resp.status_code == 201
        assert resp.json()["phone"] is None
    finally:
        _clear()


# ── 403 non-admin ─────────────────────────────────────────────────────────────


def test_create_client_rejects_non_admin_with_403() -> None:
    client = _client(admin=False)
    try:
        resp = client.post(
            "/api/v1/admin/clients",
            json={"name": "Maria", "email": "maria@test.com", "password": "Senha@123"},
        )
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "FORBIDDEN"
    finally:
        _clear()


# ── 409 duplicate email ──────────────────────────────────────────────────────


def test_create_client_email_exists_returns_409() -> None:
    gateway = _FakeGateway(uuid4(), exc=EmailAlreadyRegistered("Email já cadastrado."))
    repo = _FakeRepo()
    client = _client(_use_case(repo, gateway))
    try:
        resp = client.post(
            "/api/v1/admin/clients",
            json={"name": "Maria", "email": "maria@test.com", "password": "Senha@123"},
        )
        assert resp.status_code == 409
        assert resp.json()["error"]["code"] == "EMAIL_ALREADY_REGISTERED"
    finally:
        _clear()


# ── 422 extra field 'role' (privilege escalation guard) ──────────────────────


def test_create_client_rejects_extra_role_field() -> None:
    uid = uuid4()
    gateway = _FakeGateway(uid)
    repo = _FakeRepo()
    client = _client(_use_case(repo, gateway))
    try:
        resp = client.post(
            "/api/v1/admin/clients",
            json={
                "name": "Maria",
                "email": "maria@test.com",
                "password": "Senha@123",
                "role": "admin",
            },
        )
        assert resp.status_code in (400, 422)
        assert gateway.last_kwargs is None
    finally:
        _clear()


# ── 422 missing required field ───────────────────────────────────────────────


def test_create_client_missing_password_returns_422() -> None:
    gateway = _FakeGateway(uuid4())
    repo = _FakeRepo()
    client = _client(_use_case(repo, gateway))
    try:
        resp = client.post(
            "/api/v1/admin/clients",
            json={"name": "Maria", "email": "maria@test.com"},
        )
        assert resp.status_code in (400, 422)
    finally:
        _clear()


def test_create_client_invalid_email_returns_422() -> None:
    gateway = _FakeGateway(uuid4())
    repo = _FakeRepo()
    client = _client(_use_case(repo, gateway))
    try:
        resp = client.post(
            "/api/v1/admin/clients",
            json={"name": "Maria", "email": "not-an-email", "password": "Senha@123"},
        )
        assert resp.status_code in (400, 422)
    finally:
        _clear()


# ── 400 weak password ────────────────────────────────────────────────────────


def test_create_client_weak_password_returns_400() -> None:
    uid = uuid4()
    gateway = _FakeGateway(uid)
    repo = _FakeRepo()
    client = _client(_use_case(repo, gateway))
    try:
        resp = client.post(
            "/api/v1/admin/clients",
            json={"name": "Maria", "email": "maria@test.com", "password": "abc"},
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "VALIDATION_ERROR"
        assert gateway.last_kwargs is None
    finally:
        _clear()


# ── 500 db upsert failure post-create ────────────────────────────────────────


def test_create_client_upsert_failure_returns_500() -> None:
    uid = uuid4()
    gateway = _FakeGateway(uid)
    repo = _FakeRepo(upsert_raises=RuntimeError("DB error"))
    client = _client(_use_case(repo, gateway))
    try:
        resp = client.post(
            "/api/v1/admin/clients",
            json={"name": "Maria", "email": "maria@test.com", "password": "Senha@123"},
        )
        assert resp.status_code == 500
        assert resp.json()["error"]["code"] == "INTERNAL_ERROR"
    finally:
        _clear()


# ── upsert called with role='cliente' (security regression) ──────────────────


def test_create_client_upsert_inserts_role_cliente() -> None:
    uid = uuid4()
    gateway = _FakeGateway(uid)
    repo = _FakeRepo()
    client = _client(_use_case(repo, gateway))
    try:
        client.post(
            "/api/v1/admin/clients",
            json={"name": "Maria", "email": "maria@test.com", "password": "Senha@123"},
        )
        assert repo.upsert_called_with is not None
        assert repo.upsert_called_with.role == "cliente"
        assert repo.upsert_called_with.inactive is False
    finally:
        _clear()


# ── GET /admin/clients ───────────────────────────────────────────────────────


def test_list_clients_returns_200_with_paginated_shape() -> None:
    u1 = _make_client("Maria", "+5511999999999")
    u2 = _make_client("Joao", None)
    repo = _FakeRepo(list_result=([u1, u2], 2))
    client = _client(list_uc=_list_use_case(repo))
    try:
        resp = client.get("/api/v1/admin/clients?page=1&page_size=10")
        assert resp.status_code == 200
        data = resp.json()
        assert data["page"] == 1
        assert data["page_size"] == 10
        assert data["total"] == 2
        assert len(data["items"]) == 2
        names = {item["name"] for item in data["items"]}
        assert names == {"Maria", "Joao"}
        for item in data["items"]:
            assert set(item.keys()) == {"id", "name", "email", "phone"}
    finally:
        _clear()


def test_list_clients_uses_query_defaults() -> None:
    repo = _FakeRepo(list_result=([], 0))
    client = _client(list_uc=_list_use_case(repo))
    try:
        resp = client.get("/api/v1/admin/clients")
        assert resp.status_code == 200
        assert repo.list_called_with == (1, 50)
    finally:
        _clear()


def test_list_clients_rejects_non_admin_with_403() -> None:
    repo = _FakeRepo()
    client = _client(list_uc=_list_use_case(repo), admin=False)
    try:
        resp = client.get("/api/v1/admin/clients")
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "FORBIDDEN"
    finally:
        _clear()


def test_list_clients_rejects_page_size_over_limit() -> None:
    repo = _FakeRepo()
    client = _client(list_uc=_list_use_case(repo))
    try:
        resp = client.get("/api/v1/admin/clients?page=1&page_size=999")
        assert resp.status_code in (400, 422)
        assert repo.list_called_with is None
    finally:
        _clear()


def test_list_clients_rejects_page_zero() -> None:
    repo = _FakeRepo()
    client = _client(list_uc=_list_use_case(repo))
    try:
        resp = client.get("/api/v1/admin/clients?page=0")
        assert resp.status_code in (400, 422)
        assert repo.list_called_with is None
    finally:
        _clear()
