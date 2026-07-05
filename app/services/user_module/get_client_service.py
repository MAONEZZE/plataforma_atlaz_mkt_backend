from uuid import UUID

from app.domain.user_module.user_exceptions import UserNotFound
from app.domain.user_module.user_model import User
from app.domain.user_module.user_repo_interface import UserRepository


class GetClient:
    def __init__(self, repo: UserRepository) -> None:
        self._repo = repo

    async def execute(self, client_id: UUID) -> User:
        user = await self._repo.get_by_id(client_id)
        if user is None:
            raise UserNotFound(f"Cliente {client_id} não encontrado.")
        return user
