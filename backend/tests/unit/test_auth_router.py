"""Unit tests for POST /auth/login and POST /auth/logout endpoints."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.contexts.auth.application.dtos import TokensDTO
from app.contexts.auth.application.use_cases.login import Login
from app.contexts.auth.application.use_cases.logout import Logout
from app.contexts.auth.domain.entities import User as AuthUser
from app.contexts.auth.domain.exceptions import InvalidCredentials, LogoutFailed
from app.contexts.auth.presentation.router import _login, _logout
from app.core.deps import get_current_user
from app.main import app

_UID = uuid4()

_TOKENS = TokensDTO(
    access_token="access-token-abc",
    refresh_token="refresh-token-xyz",
    expires_in=3600,
    token_type="bearer",
)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


def _mock_login(*, return_value: object = None, side_effect: object = None) -> AsyncMock:
    m = AsyncMock(spec=Login)
    if side_effect:
        m.execute.side_effect = side_effect
    else:
        m.execute.return_value = return_value
    return m


def _mock_logout(*, side_effect: object = None) -> AsyncMock:
    m = AsyncMock(spec=Logout)
    if side_effect:
        m.execute.side_effect = side_effect
    else:
        m.execute.return_value = None
    return m


def _auth_user() -> AuthUser:
    return AuthUser(id=_UID, email="user@test.com", role="cliente", inactive=False)


# ── POST /auth/login ──────────────────────────────────────────────────────────

def test_login_ok_returns_200_with_tokens(client: TestClient) -> None:
    uc = _mock_login(return_value=_TOKENS)
    app.dependency_overrides[_login] = lambda: uc
    try:
        r = client.post(
            "/api/v1/auth/login",
            json={"email": "user@test.com", "password": "senha123"},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["access_token"] == "access-token-abc"
        assert data["refresh_token"] == "refresh-token-xyz"
        assert data["expires_in"] == 3600
        assert data["token_type"] == "bearer"
    finally:
        app.dependency_overrides.clear()


def test_login_invalid_credentials_returns_401(client: TestClient) -> None:
    uc = _mock_login(side_effect=InvalidCredentials("Email ou senha inválidos."))
    app.dependency_overrides[_login] = lambda: uc
    try:
        r = client.post(
            "/api/v1/auth/login",
            json={"email": "user@test.com", "password": "wrong"},
        )
        assert r.status_code == 401
        assert r.json()["error"]["code"] == "AUTH_FAILED"
    finally:
        app.dependency_overrides.clear()


def test_login_extra_field_rejected(client: TestClient) -> None:
    r = client.post(
        "/api/v1/auth/login",
        json={"email": "user@test.com", "password": "senha123", "unknown": "field"},
    )
    assert r.status_code in (400, 422)


def test_login_missing_fields_returns_error(client: TestClient) -> None:
    r = client.post("/api/v1/auth/login", json={"email": "user@test.com"})
    assert r.status_code in (400, 422)


# ── POST /auth/logout ─────────────────────────────────────────────────────────

def test_logout_ok_returns_204(client: TestClient) -> None:
    uc = _mock_logout()
    app.dependency_overrides[get_current_user] = lambda: _auth_user()
    app.dependency_overrides[_logout] = lambda: uc
    try:
        r = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": "Bearer access-token-abc"},
        )
        assert r.status_code == 204
    finally:
        app.dependency_overrides.clear()


def test_logout_without_token_returns_401(client: TestClient) -> None:
    r = client.post("/api/v1/auth/logout")
    assert r.status_code == 401


def test_logout_gateway_failure_returns_500(client: TestClient) -> None:
    uc = _mock_logout(side_effect=LogoutFailed("Supabase error"))
    app.dependency_overrides[get_current_user] = lambda: _auth_user()
    app.dependency_overrides[_logout] = lambda: uc
    try:
        r = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": "Bearer access-token-abc"},
        )
        assert r.status_code == 500
        assert r.json()["error"]["code"] == "INTERNAL_ERROR"
    finally:
        app.dependency_overrides.clear()
