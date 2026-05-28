from app.domain.stage_module.stage_model import Stage
from app.domain.stage_module.stage_repo_interface import StageRepository


class ListStages:
    def __init__(self, repo: StageRepository) -> None:
        self._repo = repo

    async def execute(self) -> list[Stage]:
        return await self._repo.list_all()
