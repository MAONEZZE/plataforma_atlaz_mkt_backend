from uuid import uuid4

from app.domain.shared.utils import now_sp
from app.domain.stage_module.stage_model import StageFolder
from app.domain.stage_module.stage_repo_interface import StageRepository


class CreateFolder:
    def __init__(self, repo: StageRepository) -> None:
        self._repo = repo

    async def execute(self, title: str, order: int = 0) -> StageFolder:
        folder = StageFolder(id=uuid4(), title=title, order=order, created_at=now_sp())
        return await self._repo.create_folder(folder)
