from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from app.domain.shared.base_exceptions import DomainError
from app.domain.user_module.user_exceptions import (
    EmailAlreadyRegistered,
    UserTriggerSyncFailed,
)
from app.services.user_module.create_client_service import (
    CreateClient,
    CreateClientInput,
)


def _repo() -> AsyncMock:
    mock = AsyncMock()
    mock.update.side_effect = lambda u: u
    mock.upsert_new.return_value = None
    return mock


def _gateway(user_id: UUID | None = None, side_effect: Exception | None = None) -> MagicMock:
    mock = MagicMock()
    if side_effect is not None:
        mock.create_user.side_effect = side_effect
    else:
        mock.create_user.return_value = user_id or uuid4()
    return mock


async def test_create_client_happy_path_no_phone() -> None:
    uid = uuid4()
    repo = _repo()
    gateway = _gateway(uid)

    result = await CreateClient(repo=repo, gateway=gateway).execute(
        CreateClientInput(name="Maria", email="maria@test.com", password="Senha@123")
    )

    assert result.id == uid
    assert result.name == "Maria"
    assert result.email == "maria@test.com"
    assert result.role == "cliente"
    assert result.phone is None
    repo.update.assert_not_called()


async def test_create_client_with_phone_calls_update() -> None:
    uid = uuid4()
    repo = _repo()
    gateway = _gateway(uid)

    result = await CreateClient(repo=repo, gateway=gateway).execute(
        CreateClientInput(
            name="Maria",
            email="maria@test.com",
            password="Senha@123",
            phone="+5511999999999",
        )
    )

    assert result.phone == "+5511999999999"
    repo.update.assert_awaited_once()


async def test_create_client_weak_password_raises_before_gateway() -> None:
    gateway = _gateway()
    uc = CreateClient(repo=_repo(), gateway=gateway)

    with pytest.raises(DomainError):
        await uc.execute(
            CreateClientInput(name="Maria", email="maria@test.com", password="abc")
        )

    gateway.create_user.assert_not_called()


async def test_create_client_invalid_phone_raises_before_gateway() -> None:
    gateway = _gateway()
    uc = CreateClient(repo=_repo(), gateway=gateway)

    with pytest.raises(DomainError):
        await uc.execute(
            CreateClientInput(
                name="Maria",
                email="maria@test.com",
                password="Senha@123",
                phone="abc",
            )
        )

    gateway.create_user.assert_not_called()


async def test_create_client_email_exists_propagates() -> None:
    gateway = _gateway(side_effect=EmailAlreadyRegistered("Email já cadastrado."))
    uc = CreateClient(repo=_repo(), gateway=gateway)

    with pytest.raises(EmailAlreadyRegistered):
        await uc.execute(
            CreateClientInput(name="Maria", email="maria@test.com", password="Senha@123")
        )


async def test_create_client_upsert_failure_raises_sync_failed() -> None:
    uid = uuid4()
    repo = AsyncMock()
    repo.upsert_new.side_effect = RuntimeError("DB error")
    gateway = _gateway(uid)

    with pytest.raises(UserTriggerSyncFailed):
        await CreateClient(repo=repo, gateway=gateway).execute(
            CreateClientInput(name="Maria", email="maria@test.com", password="Senha@123")
        )


async def test_create_client_calls_upsert_with_role_cliente() -> None:
    uid = uuid4()
    repo = _repo()
    gateway = _gateway(uid)

    await CreateClient(repo=repo, gateway=gateway).execute(
        CreateClientInput(name="Maria", email="maria@test.com", password="Senha@123")
    )

    repo.upsert_new.assert_awaited_once()
    user_arg = repo.upsert_new.call_args[0][0]
    assert user_arg.id == uid
    assert user_arg.role == "cliente"
    assert user_arg.inactive is False


async def test_create_client_always_passes_role_cliente() -> None:
    uid = uuid4()
    repo = _repo()
    gateway = _gateway(uid)

    await CreateClient(repo=repo, gateway=gateway).execute(
        CreateClientInput(name="Maria", email="maria@test.com", password="Senha@123")
    )

    _, kwargs = gateway.create_user.call_args
    assert kwargs["role"] == "cliente"
