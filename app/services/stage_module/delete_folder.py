from uuid import UUID

from app.domain.stage_module.stage_exceptions import StageFolderNotFound
from app.domain.stage_module.stage_repo_interface import StageRepository


class DeleteFolder:
    def __init__(self, repo: StageRepository) -> None:
        self._repo = repo

    async def execute(self, folder_id: UUID) -> None:
        folder = await self._repo.get_folder_by_id(folder_id)
        if folder is None:
            raise StageFolderNotFound(f"Stage folder {folder_id} not found.")
        await self._repo.delete_folder(folder_id)
