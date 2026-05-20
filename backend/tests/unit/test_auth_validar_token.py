from collections.abc import Callable
from uuid import UUID, uuid4

import pytest

from app.contexts.auth.application.use_cases.validate_token import ValidateToken
from app.contexts.auth.domain.entities import User
from app.contexts.auth.domain.exceptions import InactiveAccount, ExpiredToken, InvalidToken


class _FakeRepo:
    def __init__(self, user: User | None) -> None:
        self._user = user

    async def get_by_id(self, user_id: UUID) -> User | None:
        return self._user


def _decoder_ok(payload: dict[str, object]) -> Callable[[str], dict[str, object]]:
    def decode(token: str) -> dict[str, object]:
        return payload

    return decode


def _decoder_raises(exc: Exception) -> Callable[[str], dict[str, object]]:
    def decode(token: str) -> dict[str, object]:
        raise exc

    return decode


@pytest.fixture
def user_id() -> UUID:
    return uuid4()


@pytest.fixture
def active_user(user_id: UUID) -> User:
    return User(id=user_id, email="a@b.com", role="cliente", inactive=False)


@pytest.fixture
def inactive_user(user_id: UUID) -> User:
    return User(id=user_id, email="a@b.com", role="cliente", inactive=True)


async def test_valid_token_returns_user(user_id: UUID, active_user: User) -> None:
    use_case = ValidateToken(
        repo=_FakeRepo(active_user),
        jwt_decoder=_decoder_ok({"sub": str(user_id)}),
    )
    result = await use_case.execute("token")
    assert result == active_user


async def test_expired_token_raises(user_id: UUID) -> None:
    use_case = ValidateToken(
        repo=_FakeRepo(None),
        jwt_decoder=_decoder_raises(ExpiredToken("exp")),
    )
    with pytest.raises(ExpiredToken):
        await use_case.execute("token")


async def test_invalid_token_raises(user_id: UUID) -> None:
    use_case = ValidateToken(
        repo=_FakeRepo(None),
        jwt_decoder=_decoder_raises(InvalidToken("bad")),
    )
    with pytest.raises(InvalidToken):
        await use_case.execute("token")


async def test_user_not_found_raises_token_invalido(user_id: UUID) -> None:
    use_case = ValidateToken(
        repo=_FakeRepo(None),
        jwt_decoder=_decoder_ok({"sub": str(user_id)}),
    )
    with pytest.raises(InvalidToken):
        await use_case.execute("token")


async def test_inactive_user_raises_conta_inativa(user_id: UUID, inactive_user: User) -> None:
    use_case = ValidateToken(
        repo=_FakeRepo(inactive_user),
        jwt_decoder=_decoder_ok({"sub": str(user_id)}),
    )
    with pytest.raises(InactiveAccount):
        await use_case.execute("token")
