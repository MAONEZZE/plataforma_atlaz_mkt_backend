from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from supabase_auth.errors import AuthApiError

from app.domain.user_module.user_exceptions import (
    EmailAlreadyRegistered,
    SupabaseAdminError,
)
from app.services.user_module.supabase_admin_gateway import (
    SupabaseAdminUserGatewayImpl,
)


def _client(create_user_return: object = None, create_user_raise: Exception | None = None) -> MagicMock:
    client = MagicMock()
    if create_user_raise is not None:
        client.auth.admin.create_user.side_effect = create_user_raise
    else:
        client.auth.admin.create_user.return_value = create_user_return
    return client


def _auth_error(message: str, code: str | None = None) -> AuthApiError:
    try:
        return AuthApiError(message, status=422, code=code)
    except TypeError:
        exc = AuthApiError(message)
        if code is not None:
            exc.code = code  # type: ignore[attr-defined]
        return exc


def test_create_user_sends_correct_payload() -> None:
    uid = uuid4()
    response = SimpleNamespace(user=SimpleNamespace(id=str(uid)))
    client = _client(create_user_return=response)

    gateway = SupabaseAdminUserGatewayImpl(client)
    result = gateway.create_user(
        email="maria@test.com",
        password="Senha@123",
        name="Maria",
        role="cliente",
    )

    assert result == uid
    client.auth.admin.create_user.assert_called_once_with(
        {
            "email": "maria@test.com",
            "password": "Senha@123",
            "email_confirm": True,
            "user_metadata": {"name": "Maria", "role": "cliente"},
        }
    )


def test_create_user_email_exists_code_raises_email_already_registered() -> None:
    client = _client(create_user_raise=_auth_error("User already registered", code="email_exists"))
    gateway = SupabaseAdminUserGatewayImpl(client)

    with pytest.raises(EmailAlreadyRegistered):
        gateway.create_user(
            email="maria@test.com",
            password="Senha@123",
            name="Maria",
            role="cliente",
        )


def test_create_user_email_exists_message_fallback() -> None:
    client = _client(create_user_raise=_auth_error("User already registered"))
    gateway = SupabaseAdminUserGatewayImpl(client)

    with pytest.raises(EmailAlreadyRegistered):
        gateway.create_user(
            email="maria@test.com",
            password="Senha@123",
            name="Maria",
            role="cliente",
        )


def test_create_user_other_auth_error_raises_supabase_admin_error() -> None:
    client = _client(create_user_raise=_auth_error("boom", code="weak_password"))
    gateway = SupabaseAdminUserGatewayImpl(client)

    with pytest.raises(SupabaseAdminError):
        gateway.create_user(
            email="maria@test.com",
            password="Senha@123",
            name="Maria",
            role="cliente",
        )


def test_create_user_none_user_raises_supabase_admin_error() -> None:
    response = SimpleNamespace(user=None)
    client = _client(create_user_return=response)
    gateway = SupabaseAdminUserGatewayImpl(client)

    with pytest.raises(SupabaseAdminError):
        gateway.create_user(
            email="maria@test.com",
            password="Senha@123",
            name="Maria",
            role="cliente",
        )
