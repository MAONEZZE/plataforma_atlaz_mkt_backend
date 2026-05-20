from uuid import UUID

from app.contexts.users.domain.entities import User
from app.contexts.users.domain.exceptions import UserNotFound
from app.contexts.users.domain.repositories import UserRepository


class GetMe:
    def __init__(self, repo: UserRepository) -> None:
        self._repo = repo

    async def execute(self, user_id: UUID) -> User:
        user = await self._repo.get_by_id(user_id)
        if user is None:
            raise UserNotFound("Usuário não encontrado.")
        return user
