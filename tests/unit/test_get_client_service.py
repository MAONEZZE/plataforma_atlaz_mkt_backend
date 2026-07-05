from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.domain.shared.utils import now_sp
from app.domain.user_module.user_exceptions import UserNotFound
from app.domain.user_module.user_model import User
from app.services.user_module.get_client_service import GetClient


def _user() -> User:
    now = now_sp()
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
        created_at=now,
        updated_at=now,
    )


@pytest.mark.asyncio
async def test_get_client_happy_path() -> None:
    user = _user()
    repo = AsyncMock()
    repo.get_by_id.return_value = user
    result = await GetClient(repo=repo).execute(user.id)
    assert result.id == user.id
    repo.get_by_id.assert_awaited_once_with(user.id)


@pytest.mark.asyncio
async def test_get_client_not_found() -> None:
    repo = AsyncMock()
    repo.get_by_id.return_value = None
    with pytest.raises(UserNotFound):
        await GetClient(repo=repo).execute(uuid4())
