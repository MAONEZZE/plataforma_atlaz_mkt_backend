from dataclasses import replace
from uuid import UUID

from app.domain.stage_module.stage_exceptions import StageNotFound
from app.domain.stage_module.stage_model import Stage
from app.domain.stage_module.stage_repo_interface import StageRepository


class UpdateStage:
    def __init__(self, repo: StageRepository) -> None:
        self._repo = repo

    async def execute(self, stage_id: UUID, text: str) -> Stage:
        stage = await self._repo.get_by_id(stage_id)
        if stage is None:
            raise StageNotFound(f"Stage {stage_id} not found.")
        updated = replace(stage, text=text)
        return await self._repo.update(updated)
