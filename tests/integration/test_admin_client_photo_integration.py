"""Integration tests: admin photo router → real UploadPhoto use case.

Mirrors tests/integration/test_image_upload_integration.py but for the
admin-on-behalf-of-client route (POST /admin/clients/{client_id}/photo).
"""

import io
from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.api.config.dependencies.auth_deps import get_current_user, require_admin
from app.api.controllers.user_module.user_routes.admin_router import _upload_client_photo
from app.domain.auth_module.auth_model import User as AuthUser
from app.domain.user_module.user_model import User
from app.main import app
from app.services.user_module.upload_photo_service import UploadPhoto

_NOW = datetime(2024, 1, 1, tzinfo=UTC)


def _admin() -> AuthUser:
    return AuthUser(id=uuid4(), email="admin@test.com", role="admin", inactive=False)


def _cliente() -> AuthUser:
    return AuthUser(id=uuid4(), email="c@test.com", role="cliente", inactive=False)


def _client_user(user_id: UUID) -> User:
    return User(
        id=user_id,
        name="Maria",
        email="maria@test.com",
        phone=None,
        linkedin_url=None,
        instagram_username=None,
        description=None,
        photo_url=None,
        role="cliente",
        inactive=False,
        created_at=_NOW,
        updated_at=_NOW,
    )


_JPEG_BYTES = b"\xff\xd8\xff" + b"\x00" * 20


def _make_use_case(
    client_id: UUID,
    photo_url: str = "https://cdn.example.com/photo.jpg",
    found: bool = True,
) -> UploadPhoto:
    repo = AsyncMock()
    repo.get_by_id.return_value = _client_user(client_id) if found else None
    repo.update.side_effect = lambda u: u

    storage = AsyncMock()
    storage.upload.return_value = photo_url

    return UploadPhoto(repo=repo, storage=storage)


def _client(use_case: UploadPhoto | None = None, *, admin: bool = True) -> TestClient:
    if admin:
        app.dependency_overrides[require_admin] = _admin
        app.dependency_overrides[get_current_user] = _admin
    else:
        app.dependency_overrides[get_current_user] = _cliente
        app.dependency_overrides.pop(require_admin, None)
    if use_case is not None:
        app.dependency_overrides[_upload_client_photo] = lambda: use_case
    return TestClient(app, raise_server_exceptions=False)


def _clear() -> None:
    app.dependency_overrides.clear()


def test_admin_uploads_client_photo_200() -> None:
    client_id = uuid4()
    uc = _make_use_case(client_id)
    client = _client(uc)
    try:
        resp = client.post(
            f"/api/v1/admin/clients/{client_id}/photo",
            files={"photo": ("photo.jpg", io.BytesIO(_JPEG_BYTES), "image/jpeg")},
        )
        assert resp.status_code == 200
        assert resp.json()["photo_url"] == "https://cdn.example.com/photo.jpg"
    finally:
        _clear()


def test_admin_upload_client_photo_rejects_non_admin() -> None:
    client_id = uuid4()
    client = _client(admin=False)
    try:
        resp = client.post(
            f"/api/v1/admin/clients/{client_id}/photo",
            files={"photo": ("photo.jpg", io.BytesIO(_JPEG_BYTES), "image/jpeg")},
        )
        assert resp.status_code == 403
    finally:
        _clear()


def test_admin_upload_client_photo_invalid_content_type_400() -> None:
    client_id = uuid4()
    uc = _make_use_case(client_id)
    client = _client(uc)
    try:
        resp = client.post(
            f"/api/v1/admin/clients/{client_id}/photo",
            files={"photo": ("doc.pdf", io.BytesIO(b"%PDF-1.4" + b"\x00" * 20), "application/pdf")},
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "VALIDATION_ERROR"
    finally:
        _clear()


def test_admin_upload_client_photo_client_not_found_404() -> None:
    client_id = uuid4()
    uc = _make_use_case(client_id, found=False)
    client = _client(uc)
    try:
        resp = client.post(
            f"/api/v1/admin/clients/{client_id}/photo",
            files={"photo": ("photo.jpg", io.BytesIO(_JPEG_BYTES), "image/jpeg")},
        )
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "CLIENT_NOT_FOUND"
    finally:
        _clear()


def test_admin_upload_client_photo_over_5mb_400() -> None:
    client_id = uuid4()
    uc = _make_use_case(client_id)
    client = _client(uc)
    big_jpeg = b"\xff\xd8\xff" + b"\x00" * (5 * 1024 * 1024 + 1)
    try:
        resp = client.post(
            f"/api/v1/admin/clients/{client_id}/photo",
            files={"photo": ("big.jpg", io.BytesIO(big_jpeg), "image/jpeg")},
        )
        assert resp.status_code == 400
    finally:
        _clear()
