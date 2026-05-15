"""Tests for the /me router endpoints via TestClient with mocked use cases."""

import io
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.contexts.auth.domain.entities import Usuario as AuthUsuario
from app.contexts.usuarios.application.dtos import FotoUrlDTO
from app.contexts.usuarios.application.use_cases.atualizar_me import AtualizarMe
from app.contexts.usuarios.application.use_cases.obter_me import ObterMe
from app.contexts.usuarios.application.use_cases.upload_foto import UploadFoto
from app.contexts.usuarios.domain.entities import Usuario
from app.contexts.usuarios.domain.exceptions import FotoInvalida, UsuarioNaoEncontrado
from app.contexts.usuarios.presentation.router import (
    _atualizar_me,
    _obter_me,
    _upload_foto,
    router,
)
from app.core.deps import get_current_user
from app.core.exceptions import AppException
from app.shared.domain.exceptions import DomainError

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


def _auth_user(role: str = "cliente") -> AuthUsuario:
    return AuthUsuario(id=_UID, email="ana@test.com", role=role, inativo=False)


def _domain_user() -> Usuario:
    return Usuario(
        id=_UID,
        nome="Ana",
        email="ana@test.com",
        telefone=None,
        linkedin_url=None,
        instagram_username=None,
        foto_url=None,
        role="cliente",
        inativo=False,
        criado_em=_NOW,
        atualizado_em=_NOW,
    )


def _mock_use_case(spec: type, *, return_value: Any = None, side_effect: Any = None) -> Any:
    mock = AsyncMock(spec=spec)
    if side_effect:
        mock.execute.side_effect = side_effect
    else:
        mock.execute.return_value = return_value
    return mock


def _client(
    obter: Any = None,
    atualizar: Any = None,
    upload: Any = None,
    role: str = "cliente",
) -> TestClient:
    user = _auth_user(role)
    _app.dependency_overrides[get_current_user] = lambda: user
    if obter is not None:
        _app.dependency_overrides[_obter_me] = lambda: obter
    if atualizar is not None:
        _app.dependency_overrides[_atualizar_me] = lambda: atualizar
    if upload is not None:
        _app.dependency_overrides[_upload_foto] = lambda: upload
    return TestClient(_app, raise_server_exceptions=False)


def _clear() -> None:
    _app.dependency_overrides.clear()


# ── GET /me ───────────────────────────────────────────────────────────────────


def test_get_me_returns_200() -> None:
    uc = _mock_use_case(ObterMe, return_value=_domain_user())
    client = _client(obter=uc)
    try:
        resp = client.get("/api/v1/me")
        assert resp.status_code == 200
        data = resp.json()
        assert data["nome"] == "Ana"
        assert data["email"] == "ana@test.com"
        assert "telefone" in data
    finally:
        _clear()


def test_get_me_not_found_returns_404() -> None:
    uc = _mock_use_case(ObterMe, side_effect=UsuarioNaoEncontrado("x"))
    client = _client(obter=uc)
    try:
        resp = client.get("/api/v1/me")
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "RESOURCE_NOT_FOUND"
    finally:
        _clear()


# ── PATCH /me ─────────────────────────────────────────────────────────────────


def test_patch_me_returns_200() -> None:
    updated = _domain_user()
    updated.nome = "Beatriz"
    uc = _mock_use_case(AtualizarMe, return_value=updated)
    client = _client(atualizar=uc)
    try:
        resp = client.patch("/api/v1/me", json={"nome": "Beatriz"})
        assert resp.status_code == 200
        assert resp.json()["nome"] == "Beatriz"
    finally:
        _clear()


def test_patch_me_rejects_email_field() -> None:
    uc = _mock_use_case(AtualizarMe, return_value=_domain_user())
    client = _client(atualizar=uc)
    try:
        resp = client.patch("/api/v1/me", json={"email": "novo@test.com"})
        assert resp.status_code == 422
    finally:
        _clear()


def test_patch_me_domain_error_returns_400() -> None:
    uc = _mock_use_case(AtualizarMe, side_effect=DomainError("LinkedIn URL inválida."))
    client = _client(atualizar=uc)
    try:
        resp = client.patch("/api/v1/me", json={"linkedin_url": "https://twitter.com/x"})
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "VALIDATION_ERROR"
    finally:
        _clear()


def test_patch_me_not_found_returns_404() -> None:
    uc = _mock_use_case(AtualizarMe, side_effect=UsuarioNaoEncontrado("x"))
    client = _client(atualizar=uc)
    try:
        resp = client.patch("/api/v1/me", json={"nome": "X"})
        assert resp.status_code == 404
    finally:
        _clear()


# ── POST /me/foto ─────────────────────────────────────────────────────────────

_JPEG_BYTES = b"\xff\xd8\xff" + b"\x00" * 10


def test_post_foto_returns_200() -> None:
    uc = _mock_use_case(UploadFoto, return_value=FotoUrlDTO(foto_url="https://cdn.x/foto.jpg"))
    client = _client(upload=uc)
    try:
        resp = client.post(
            "/api/v1/me/foto",
            files={"foto": ("foto.jpg", io.BytesIO(_JPEG_BYTES), "image/jpeg")},
        )
        assert resp.status_code == 200
        assert resp.json()["foto_url"].startswith("https://")
    finally:
        _clear()


def test_post_foto_invalid_returns_400() -> None:
    uc = _mock_use_case(UploadFoto, side_effect=FotoInvalida("Tipo não suportado."))
    client = _client(upload=uc)
    try:
        resp = client.post(
            "/api/v1/me/foto",
            files={"foto": ("doc.pdf", io.BytesIO(b"fake"), "application/pdf")},
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "VALIDATION_ERROR"
    finally:
        _clear()


def test_post_foto_user_not_found_returns_404() -> None:
    uc = _mock_use_case(UploadFoto, side_effect=UsuarioNaoEncontrado("x"))
    client = _client(upload=uc)
    try:
        resp = client.post(
            "/api/v1/me/foto",
            files={"foto": ("f.jpg", io.BytesIO(_JPEG_BYTES), "image/jpeg")},
        )
        assert resp.status_code == 404
    finally:
        _clear()
