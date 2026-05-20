from typing import Any
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.contexts.auth.application.use_cases.validate_token import ValidateToken
from app.contexts.auth.domain.entities import User
from app.contexts.auth.domain.exceptions import InactiveAccount, ExpiredToken, InvalidToken
from app.contexts.auth.presentation.deps import get_validate_token_use_case
from app.core.deps import get_current_user, require_admin
from app.core.exceptions import AppException

# ── Minimal test app with exception handler ───────────────────────────────────

_app = FastAPI()


@_app.exception_handler(AppException)
async def _exc_handler(request: Request, exc: AppException) -> JSONResponse:
    body: dict[str, Any] = {"error": {"code": exc.code, "message": exc.message}}
    if exc.details:
        body["error"]["details"] = exc.details
    return JSONResponse(status_code=exc.status, content=body)


@_app.get("/me")
async def _me(user: User = Depends(get_current_user)) -> dict[str, str]:
    return {"id": str(user.id), "role": user.role}


@_app.get("/admin-only")
async def _admin_only(user: User = Depends(require_admin)) -> dict[str, str]:
    return {"id": str(user.id)}


# ── Helpers ───────────────────────────────────────────────────────────────────


def _mock_use_case(*, user: User | None = None, exc: Exception | None = None) -> ValidateToken:
    mock: ValidateToken = AsyncMock(spec=ValidateToken)  # type: ignore[assignment]
    if exc:
        mock.execute.side_effect = exc  # type: ignore[attr-defined]
    else:
        mock.execute.return_value = user  # type: ignore[attr-defined]
    return mock


def _client(use_case: ValidateToken) -> TestClient:
    _app.dependency_overrides[get_validate_token_use_case] = lambda: use_case
    return TestClient(_app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def _clear_overrides() -> None:
    yield
    _app.dependency_overrides.clear()


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def cliente_user() -> User:
    return User(id=uuid4(), email="c@c.com", role="cliente", inactive=False)


@pytest.fixture
def admin_user() -> User:
    return User(id=uuid4(), email="a@a.com", role="admin", inactive=False)


# ── Tests ─────────────────────────────────────────────────────────────────────


def test_no_token_returns_401() -> None:
    client = _client(_mock_use_case(exc=InvalidToken("x")))
    resp = client.get("/me")
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "TOKEN_INVALID"


def test_valid_token_active_user_returns_200(cliente_user: User) -> None:
    client = _client(_mock_use_case(user=cliente_user))
    resp = client.get("/me", headers={"Authorization": "Bearer valid"})
    assert resp.status_code == 200
    assert resp.json()["role"] == "cliente"


def test_expired_token_returns_401_token_expired() -> None:
    client = _client(_mock_use_case(exc=ExpiredToken("exp")))
    resp = client.get("/me", headers={"Authorization": "Bearer expired"})
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "TOKEN_EXPIRED"


def test_invalid_token_returns_401_token_invalid() -> None:
    client = _client(_mock_use_case(exc=InvalidToken("bad")))
    resp = client.get("/me", headers={"Authorization": "Bearer bad"})
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "TOKEN_INVALID"


def test_inactive_user_returns_403() -> None:
    client = _client(_mock_use_case(exc=InactiveAccount()))
    resp = client.get("/me", headers={"Authorization": "Bearer token"})
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "AUTH_INACTIVE_ACCOUNT"


def test_require_admin_with_cliente_returns_403(cliente_user: User) -> None:
    client = _client(_mock_use_case(user=cliente_user))
    resp = client.get("/admin-only", headers={"Authorization": "Bearer token"})
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "FORBIDDEN"


def test_require_admin_with_admin_returns_200(admin_user: User) -> None:
    client = _client(_mock_use_case(user=admin_user))
    resp = client.get("/admin-only", headers={"Authorization": "Bearer token"})
    assert resp.status_code == 200
