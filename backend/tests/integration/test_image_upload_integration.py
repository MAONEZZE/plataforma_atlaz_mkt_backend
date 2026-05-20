"""Integration tests: router → real UploadFoto use case → real detect_image_mime.

Repo and storage are mocked; the use case itself is NOT mocked so that
detect_image_mime is exercised end-to-end through the HTTP layer.
"""

import io
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.contexts.auth.domain.entities import User as AuthUser
from app.contexts.users.application.dtos import PhotoUrlDTO
from app.contexts.users.application.use_cases.upload_photo import UploadPhoto
from app.contexts.users.domain.entities import User
from app.contexts.users.presentation.router import _upload_foto, router
from app.core.deps import get_current_user
from app.core.exceptions import AppException

_NOW = datetime(2024, 1, 1, tzinfo=UTC)
_UID = uuid4()

_app = FastAPI()
_app.include_router(router, prefix="/api/v1")


@_app.exception_handler(AppException)
async def _exc(request: Request, exc: AppException) -> JSONResponse:
    body: dict[str, Any] = {"error": {"code": exc.code, "message": exc.message}}
    return JSONResponse(status_code=exc.status, content=body)


_AUTH_USER = AuthUser(id=_UID, email="ana@test.com", role="cliente", inativo=False)

_DOMAIN_USER = Usuario(
    id=_UID,
    nome="Ana",
    email="ana@test.com",
    telefone=None,
    linkedin_url=None,
    instagram_username=None,
    descricao=None,
    foto_url=None,
    role="cliente",
    inativo=False,
    criado_em=_NOW,
    atualizado_em=_NOW,
)

# ── Magic bytes for each format ───────────────────────────────────────────────

_JPEG_BYTES = b"\xff\xd8\xff" + b"\x00" * 20
_PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 20
_WEBP_BYTES = b"RIFF\x00\x00\x00\x00WEBP" + b"\x00" * 20
_PHP_BYTES = b"<?php echo 'hello'; ?>" + b"\x00" * 20
_UNKNOWN_BYTES = b"FAKEFAKEFAKE" + b"\x00" * 20


def _make_upload_use_case(foto_url: str = "https://cdn.example.com/foto.jpg") -> UploadPhoto:
    """Real UploadFoto with mocked repo + storage."""
    repo = AsyncMock()
    repo.por_id.return_value = _DOMAIN_USER
    repo.atualizar.side_effect = lambda u: u

    storage = MagicMock()
    storage.upload.return_value = foto_url

    return UploadPhoto(repo=repo, storage=storage)


def _client(use_case: UploadPhoto) -> TestClient:
    _app.dependency_overrides[get_current_user] = lambda: _AUTH_USER
    _app.dependency_overrides[_upload_foto] = lambda: use_case
    return TestClient(_app, raise_server_exceptions=False)


def _clear() -> None:
    _app.dependency_overrides.clear()


# ── Happy path ────────────────────────────────────────────────────────────────


def test_valid_jpeg_returns_200() -> None:
    uc = _make_upload_use_case()
    client = _client(uc)
    try:
        resp = client.post(
            "/api/v1/me/foto",
            files={"foto": ("photo.jpg", io.BytesIO(_JPEG_BYTES), "image/jpeg")},
        )
        assert resp.status_code == 200
        assert "foto_url" in resp.json()
    finally:
        _clear()


def test_valid_png_returns_200() -> None:
    uc = _make_upload_use_case("https://cdn.example.com/foto.png")
    client = _client(uc)
    try:
        resp = client.post(
            "/api/v1/me/foto",
            files={"foto": ("photo.png", io.BytesIO(_PNG_BYTES), "image/png")},
        )
        assert resp.status_code == 200
    finally:
        _clear()


def test_valid_webp_returns_200() -> None:
    uc = _make_upload_use_case("https://cdn.example.com/foto.webp")
    client = _client(uc)
    try:
        resp = client.post(
            "/api/v1/me/foto",
            files={"foto": ("photo.webp", io.BytesIO(_WEBP_BYTES), "image/webp")},
        )
        assert resp.status_code == 200
    finally:
        _clear()


# ── Magic bytes mismatch ──────────────────────────────────────────────────────


def test_php_renamed_as_jpg_returns_400() -> None:
    """PHP file renamed to .jpg must be rejected via magic byte check."""
    uc = _make_upload_use_case()
    client = _client(uc)
    try:
        resp = client.post(
            "/api/v1/me/foto",
            files={"foto": ("shell.jpg", io.BytesIO(_PHP_BYTES), "image/jpeg")},
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "VALIDATION_ERROR"
    finally:
        _clear()


def test_unknown_bytes_claimed_as_jpeg_returns_400() -> None:
    uc = _make_upload_use_case()
    client = _client(uc)
    try:
        resp = client.post(
            "/api/v1/me/foto",
            files={"foto": ("bad.jpg", io.BytesIO(_UNKNOWN_BYTES), "image/jpeg")},
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "VALIDATION_ERROR"
    finally:
        _clear()


def test_jpeg_bytes_claimed_as_png_returns_400() -> None:
    """Valid JPEG magic but wrong declared content-type → rejected."""
    uc = _make_upload_use_case()
    client = _client(uc)
    try:
        resp = client.post(
            "/api/v1/me/foto",
            files={"foto": ("photo.png", io.BytesIO(_JPEG_BYTES), "image/png")},
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "VALIDATION_ERROR"
    finally:
        _clear()


def test_png_bytes_claimed_as_jpeg_returns_400() -> None:
    uc = _make_upload_use_case()
    client = _client(uc)
    try:
        resp = client.post(
            "/api/v1/me/foto",
            files={"foto": ("photo.jpg", io.BytesIO(_PNG_BYTES), "image/jpeg")},
        )
        assert resp.status_code == 400
    finally:
        _clear()


# ── Size limit ────────────────────────────────────────────────────────────────


def test_jpeg_over_5mb_returns_400() -> None:
    """File exceeding 5 MB must be rejected before any storage call."""
    big_jpeg = b"\xff\xd8\xff" + b"\x00" * (5 * 1024 * 1024 + 1)
    uc = _make_upload_use_case()
    client = _client(uc)
    try:
        resp = client.post(
            "/api/v1/me/foto",
            files={"foto": ("big.jpg", io.BytesIO(big_jpeg), "image/jpeg")},
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "VALIDATION_ERROR"
    finally:
        _clear()


def test_jpeg_exactly_5mb_is_accepted() -> None:
    """Exactly 5 MB (not exceeding) must be accepted."""
    exact_jpeg = b"\xff\xd8\xff" + b"\x00" * (5 * 1024 * 1024 - 3)
    uc = _make_upload_use_case()
    client = _client(uc)
    try:
        resp = client.post(
            "/api/v1/me/foto",
            files={"foto": ("exact.jpg", io.BytesIO(exact_jpeg), "image/jpeg")},
        )
        assert resp.status_code == 200
    finally:
        _clear()


# ── Unsupported MIME type ─────────────────────────────────────────────────────


def test_pdf_content_type_returns_400() -> None:
    uc = _make_upload_use_case()
    client = _client(uc)
    try:
        resp = client.post(
            "/api/v1/me/foto",
            files={"foto": ("doc.pdf", io.BytesIO(b"%PDF-1.4" + b"\x00" * 20), "application/pdf")},
        )
        assert resp.status_code == 400
    finally:
        _clear()
