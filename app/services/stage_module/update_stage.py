from dataclasses import replace
from uuid import UUID

from app.domain.stage_module.stage_exceptions import StageNotFound
from app.domain.stage_module.stage_model import Stage
from app.domain.stage_module.stage_repo_interface import StageRepository


class UpdateStage:
    def __init__(self, repo: StageRepository) -> None:
        self._repo = repo

    async def execute(self, stage_id: UUID, text: str | None = None, stage_title: str | None = None) -> Stage:
        stage = await self._repo.get_by_id(stage_id)
        if stage is None:
            raise StageNotFound(f"Stage {stage_id} not found.")
        updated = replace(
            stage,
            text=text if text is not None else stage.text,
            stage_title=stage_title if stage_title is not None else stage.stage_title,
        )
        return await self._repo.update(updated)
