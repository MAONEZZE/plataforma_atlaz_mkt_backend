from dataclasses import replace
from typing import Any
from uuid import UUID

from app.domain.stage_module.stage_exceptions import StageNotFound
from app.domain.stage_module.stage_model import Stage
from app.domain.stage_module.stage_repo_interface import StageRepository

_UNSET: Any = object()


class UpdateStage:
    def __init__(self, repo: StageRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        stage_id: UUID,
        text: str | None = None,
        title: str | None = None,
        folder_id: UUID | None = _UNSET,
        order: int | None = None,
    ) -> Stage:
        stage = await self._repo.get_by_id(stage_id)
        if stage is None:
            raise StageNotFound(f"Stage {stage_id} not found.")
        updated = replace(
            stage,
            text=text if text is not None else stage.text,
            title=title if title is not None else stage.title,
            folder_id=stage.folder_id if folder_id is _UNSET else folder_id,
            order=order if order is not None else stage.order,
        )
        return await self._repo.update(updated)
