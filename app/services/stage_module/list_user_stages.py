from uuid import UUID

from app.domain.stage_module.stage_model import UserStage
from app.domain.stage_module.stage_repo_interface import StageRepository


class ListUserStages:
    def __init__(self, repo: StageRepository) -> None:
        self._repo = repo

    async def execute(self, user_id: UUID) -> list[UserStage]:
        return await self._repo.list_for_user(user_id)
