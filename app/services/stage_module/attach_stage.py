from uuid import UUID

from app.domain.stage_module.stage_exceptions import StageAlreadyAttached, StageNotFound
from app.domain.stage_module.stage_model import UserStage
from app.domain.stage_module.stage_repo_interface import StageRepository


class AttachStage:
    def __init__(self, repo: StageRepository) -> None:
        self._repo = repo

    async def execute(self, user_id: UUID, stage_id: UUID) -> UserStage:
        stage = await self._repo.get_by_id(stage_id)
        if stage is None:
            raise StageNotFound(f"Stage {stage_id} not found.")
        return await self._repo.attach_to_user(user_id, stage_id)
