"""Tests for the /me router endpoints via TestClient with mocked use cases."""

import io
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.api.config.dependencies.auth_deps import get_current_user
from app.api.controllers.user_module.user_dto.user_dto import PhotoUrlDTO
from app.api.controllers.user_module.user_routes.user_router import (
    _get_me,
    _update_me,
    _upload_photo,
    router,
)
from app.domain.auth_module.auth_model import User as AuthUser
from app.domain.shared.base_exceptions import AppException, DomainError
from app.domain.user_module.user_exceptions import InvalidPhoto, UserNotFound
from app.domain.user_module.user_model import User
from app.services.user_module.user_service.get_me_service import GetMe
from app.services.user_module.user_service.update_me_service import UpdateMe
from app.services.user_module.user_service.upload_photo_service import UploadPhoto

_NOW = datetime(2024, 1, 1, tzinfo=UTC)
_UID = uuid4()

# ── Minimal test app ─────────────────────────────────────────────────────────

_app = FastAPI()
_app.include_router(router, prefix="/api/v1")


@_app.exception_handler(AppException)
async def _exc(request: Request, exc: AppException) -> JSONResponse:
    body: dict[str, Any] = {"error": {"code": exc.code, "message": exc.message}}
    return JSONResponse(status_code=exc.status, content=body)


# ── Helpers ───────────────────────────────────────────────────────────────────


def _auth_user(role: str = "cliente") -> AuthUser:
    return AuthUser(id=_UID, email="ana@test.com", role=role, inactive=False)


def _domain_user() -> User:
    return User(
        id=_UID,
        name="Ana",
        email="ana@test.com",
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


def _mock_use_case(spec: type, *, return_value: Any = None, side_effect: Any = None) -> Any:
    mock = AsyncMock(spec=spec)
    if side_effect:
        mock.execute.side_effect = side_effect
    else:
        mock.execute.return_value = return_value
    return mock


def _client(
    get: Any = None,
    update: Any = None,
    upload: Any = None,
    role: str = "cliente",
) -> TestClient:
    user = _auth_user(role)
    _app.dependency_overrides[get_current_user] = lambda: user
    if get is not None:
        _app.dependency_overrides[_get_me] = lambda: get
    if update is not None:
        _app.dependency_overrides[_update_me] = lambda: update
    if upload is not None:
        _app.dependency_overrides[_upload_photo] = lambda: upload
    return TestClient(_app, raise_server_exceptions=False)


def _clear() -> None:
    _app.dependency_overrides.clear()


# ── GET /me ───────────────────────────────────────────────────────────────────


def test_get_me_returns_200() -> None:
    uc = _mock_use_case(GetMe, return_value=_domain_user())
    client = _client(get=uc)
    try:
        resp = client.get("/api/v1/me")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Ana"
        assert data["email"] == "ana@test.com"
        assert "phone" in data
    finally:
        _clear()


def test_get_me_not_found_returns_404() -> None:
    uc = _mock_use_case(GetMe, side_effect=UserNotFound("x"))
    client = _client(get=uc)
    try:
        resp = client.get("/api/v1/me")
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "RESOURCE_NOT_FOUND"
    finally:
        _clear()


# ── PATCH /me ─────────────────────────────────────────────────────────────────


def test_patch_me_returns_200() -> None:
    updated = _domain_user()
    updated.name = "Beatriz"
    uc = _mock_use_case(UpdateMe, return_value=updated)
    client = _client(update=uc)
    try:
        resp = client.patch("/api/v1/me", json={"name": "Beatriz"})
        assert resp.status_code == 200
        assert resp.json()["name"] == "Beatriz"
    finally:
        _clear()


def test_patch_me_updates_description() -> None:
    updated = _domain_user()
    updated.description = "Professional trader."
    uc = _mock_use_case(UpdateMe, return_value=updated)
    client = _client(update=uc)
    try:
        resp = client.patch("/api/v1/me", json={"description": "Professional trader."})
        assert resp.status_code == 200
        assert resp.json()["description"] == "Professional trader."
    finally:
        _clear()


def test_get_me_returns_description_field() -> None:
    user = _domain_user()
    user.description = "User bio."
    uc = _mock_use_case(GetMe, return_value=user)
    client = _client(get=uc)
    try:
        resp = client.get("/api/v1/me")
        assert resp.status_code == 200
        assert "description" in resp.json()
    finally:
        _clear()


def test_patch_me_rejects_email_field() -> None:
    uc = _mock_use_case(UpdateMe, return_value=_domain_user())
    client = _client(update=uc)
    try:
        resp = client.patch("/api/v1/me", json={"email": "new@test.com"})
        assert resp.status_code == 422
    finally:
        _clear()


def test_patch_me_domain_error_returns_400() -> None:
    uc = _mock_use_case(UpdateMe, side_effect=DomainError("LinkedIn URL inválida."))
    client = _client(update=uc)
    try:
        resp = client.patch("/api/v1/me", json={"linkedin_url": "https://twitter.com/x"})
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "VALIDATION_ERROR"
    finally:
        _clear()


def test_patch_me_not_found_returns_404() -> None:
    uc = _mock_use_case(UpdateMe, side_effect=UserNotFound("x"))
    client = _client(update=uc)
    try:
        resp = client.patch("/api/v1/me", json={"name": "X"})
        assert resp.status_code == 404
    finally:
        _clear()


# ── POST /me/photo ────────────────────────────────────────────────────────────

_JPEG_BYTES = b"\xff\xd8\xff" + b"\x00" * 10


def test_post_photo_returns_200() -> None:
    uc = _mock_use_case(UploadPhoto, return_value=PhotoUrlDTO(photo_url="https://cdn.x/photo.jpg"))
    client = _client(upload=uc)
    try:
        resp = client.post(
            "/api/v1/me/photo",
            files={"photo": ("photo.jpg", io.BytesIO(_JPEG_BYTES), "image/jpeg")},
        )
        assert resp.status_code == 200
        assert resp.json()["photo_url"].startswith("https://")
    finally:
        _clear()


def test_post_photo_invalid_returns_400() -> None:
    uc = _mock_use_case(UploadPhoto, side_effect=InvalidPhoto("Tipo não suportado."))
    client = _client(upload=uc)
    try:
        resp = client.post(
            "/api/v1/me/photo",
            files={"photo": ("doc.pdf", io.BytesIO(b"fake"), "application/pdf")},
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "VALIDATION_ERROR"
    finally:
        _clear()


def test_post_photo_user_not_found_returns_404() -> None:
    uc = _mock_use_case(UploadPhoto, side_effect=UserNotFound("x"))
    client = _client(upload=uc)
    try:
        resp = client.post(
            "/api/v1/me/photo",
            files={"photo": ("f.jpg", io.BytesIO(_JPEG_BYTES), "image/jpeg")},
        )
        assert resp.status_code == 404
    finally:
        _clear()
