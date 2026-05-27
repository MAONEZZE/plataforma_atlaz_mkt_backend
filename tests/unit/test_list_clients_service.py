from unittest.mock import AsyncMock
from uuid import uuid4

from app.domain.shared.utils import now_sp
from app.domain.user_module.user_model import User
from app.services.user_module.list_clients_service import (
    ListClients,
    ListClientsInput,
)


def _user(name: str = "Maria") -> User:
    now = now_sp()
    return User(
        id=uuid4(),
        name=name,
        email=f"{name.lower()}@test.com",
        phone="+5511999999999",
        linkedin_url=None,
        instagram_username=None,
        description=None,
        photo_url=None,
        role="cliente",
        inactive=False,
        created_at=now,
        updated_at=now,
    )


async def test_list_clients_empty() -> None:
    repo = AsyncMock()
    repo.list_clients.return_value = ([], 0)

    items, total = await ListClients(repo=repo).execute(
        ListClientsInput(page=1, page_size=50)
    )

    assert items == []
    assert total == 0
    repo.list_clients.assert_awaited_once_with(1, 50)


async def test_list_clients_returns_items_and_total() -> None:
    users = [_user("Maria"), _user("Joao")]
    repo = AsyncMock()
    repo.list_clients.return_value = (users, 2)

    items, total = await ListClients(repo=repo).execute(
        ListClientsInput(page=1, page_size=10)
    )

    assert items == users
    assert total == 2


async def test_list_clients_forwards_pagination_args() -> None:
    repo = AsyncMock()
    repo.list_clients.return_value = ([], 0)

    await ListClients(repo=repo).execute(ListClientsInput(page=3, page_size=20))

    repo.list_clients.assert_awaited_once_with(3, 20)
