from dataclasses import dataclass

from app.domain.user_module.user_model import User
from app.domain.user_module.user_repo_interface import UserRepository


@dataclass(frozen=True)
class ListClientsInput:
    page: int
    page_size: int


class ListClients:
    def __init__(self, repo: UserRepository) -> None:
        self._repo = repo

    async def execute(self, inp: ListClientsInput) -> tuple[list[User], int]:
        return await self._repo.list_clients(inp.page, inp.page_size)
