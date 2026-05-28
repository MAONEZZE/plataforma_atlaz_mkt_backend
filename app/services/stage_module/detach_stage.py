from uuid import UUID

from app.domain.stage_module.stage_repo_interface import StageRepository


class DetachStage:
    def __init__(self, repo: StageRepository) -> None:
        self._repo = repo

    async def execute(self, user_id: UUID, stage_id: UUID) -> None:
        await self._repo.detach_from_user(user_id, stage_id)
