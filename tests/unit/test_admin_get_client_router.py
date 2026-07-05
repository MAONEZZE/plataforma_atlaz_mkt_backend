from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.config.dependencies.auth_deps import get_current_user, require_admin
from app.api.controllers.user_module.user_routes.admin_router import _get_client, _stage_repo
from app.domain.auth_module.auth_model import User as AuthUser
from app.domain.user_module.user_exceptions import UserNotFound
from app.domain.user_module.user_model import User
from app.main import app

NOW = datetime.now(tz=UTC)


def _admin() -> AuthUser:
    return AuthUser(id=uuid4(), email="a@test.com", role="admin", inactive=False)


def _cliente() -> AuthUser:
    return AuthUser(id=uuid4(), email="c@test.com", role="cliente", inactive=False)


def _domain_user() -> User:
    return User(
        id=uuid4(),
        name="Maria",
        email="maria@test.com",
        phone=None,
        linkedin_url=None,
        instagram_username=None,
        description="desc",
        photo_url=None,
        role="cliente",
        inactive=False,
        created_at=NOW,
        updated_at=NOW,
    )


@pytest.fixture
def client() -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


def test_get_client_200(client: TestClient) -> None:
    uc = AsyncMock()
    uc.execute.return_value = _domain_user()
    stage_repo = AsyncMock()
    stage_repo.list_for_user.return_value = []
    app.dependency_overrides[require_admin] = _admin
    app.dependency_overrides[_get_client] = lambda: uc
    app.dependency_overrides[_stage_repo] = lambda: stage_repo
    try:
        r = client.get(f"/api/v1/admin/clients/{uuid4()}")
        assert r.status_code == 200
        assert r.json()["name"] == "Maria"
        assert r.json()["stages"] == []
    finally:
        app.dependency_overrides.clear()


def test_get_client_404(client: TestClient) -> None:
    uc = AsyncMock()
    uc.execute.side_effect = UserNotFound("nope")
    stage_repo = AsyncMock()
    app.dependency_overrides[require_admin] = _admin
    app.dependency_overrides[_get_client] = lambda: uc
    app.dependency_overrides[_stage_repo] = lambda: stage_repo
    try:
        r = client.get(f"/api/v1/admin/clients/{uuid4()}")
        assert r.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_get_client_403_for_cliente(client: TestClient) -> None:
    app.dependency_overrides[get_current_user] = _cliente
    try:
        r = client.get(f"/api/v1/admin/clients/{uuid4()}")
        assert r.status_code == 403
    finally:
        app.dependency_overrides.clear()
