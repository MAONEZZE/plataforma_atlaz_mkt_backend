from dataclasses import replace
from uuid import UUID

from app.domain.stage_module.stage_exceptions import StageFolderNotFound
from app.domain.stage_module.stage_model import StageFolder
from app.domain.stage_module.stage_repo_interface import StageRepository


class UpdateFolder:
    def __init__(self, repo: StageRepository) -> None:
        self._repo = repo

    async def execute(
        self, folder_id: UUID, title: str | None = None, order: int | None = None
    ) -> StageFolder:
        folder = await self._repo.get_folder_by_id(folder_id)
        if folder is None:
            raise StageFolderNotFound(f"Stage folder {folder_id} not found.")
        updated = replace(
            folder,
            title=title if title is not None else folder.title,
            order=order if order is not None else folder.order,
        )
        return await self._repo.update_folder(updated)
