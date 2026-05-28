from uuid import UUID

from app.domain.stage_module.stage_model import UserStage
from app.domain.stage_module.stage_repo_interface import StageRepository


class SetStageDone:
    def __init__(self, repo: StageRepository) -> None:
        self._repo = repo

    async def execute(self, user_id: UUID, stage_id: UUID, done: bool) -> UserStage:
        return await self._repo.set_done(user_id, stage_id, done)
