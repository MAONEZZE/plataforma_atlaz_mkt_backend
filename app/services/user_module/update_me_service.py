from uuid import UUID

from app.api.controllers.user_module.user_dto.user_dto import UpdateMeInput
from app.domain.user_module.user_exceptions import UserNotFound
from app.domain.user_module.user_model import User
from app.domain.user_module.user_repo_interface import UserRepository
from app.domain.user_module.user_validator import InstagramUsername, LinkedinUrl, Telefone


class UpdateMe:
    def __init__(self, repo: UserRepository) -> None:
        self._repo = repo

    async def execute(self, user_id: UUID, inp: UpdateMeInput) -> User:
        user = await self._repo.get_by_id(user_id)
        if user is None:
            raise UserNotFound("Usuário não encontrado.")

        if inp.name is not None:
            user.name = inp.name
        if inp.phone is not None:
            Telefone(inp.phone)
            user.phone = inp.phone
        if inp.linkedin_url is not None:
            LinkedinUrl(inp.linkedin_url)
            user.linkedin_url = inp.linkedin_url
        if inp.instagram_username is not None:
            InstagramUsername(inp.instagram_username)
            user.instagram_username = inp.instagram_username
        if inp.description is not None:
            user.description = inp.description

        return await self._repo.update(user)
