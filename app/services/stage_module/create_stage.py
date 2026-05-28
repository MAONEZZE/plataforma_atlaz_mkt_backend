from uuid import uuid4

from app.domain.shared.utils import now_sp
from app.domain.stage_module.stage_model import Stage
from app.domain.stage_module.stage_repo_interface import StageRepository


class CreateStage:
    def __init__(self, repo: StageRepository) -> None:
        self._repo = repo

    async def execute(self, text: str) -> Stage:
        stage = Stage(id=uuid4(), text=text, created_at=now_sp())
        return await self._repo.create(stage)
