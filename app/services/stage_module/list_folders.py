from app.domain.stage_module.stage_model import StageFolder
from app.domain.stage_module.stage_repo_interface import StageRepository


class ListFolders:
    def __init__(self, repo: StageRepository) -> None:
        self._repo = repo

    async def execute(self) -> list[StageFolder]:
        return await self._repo.list_folders()
