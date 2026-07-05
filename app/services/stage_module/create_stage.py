from uuid import UUID, uuid4

from app.domain.shared.utils import now_sp
from app.domain.stage_module.stage_model import Stage
from app.domain.stage_module.stage_repo_interface import StageRepository


class CreateStage:
    def __init__(self, repo: StageRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        text: str,
        title: str | None = None,
        folder_id: UUID | None = None,
        order: int = 0,
    ) -> Stage:
        stage = Stage(
            id=uuid4(),
            text=text,
            title=title,
            created_at=now_sp(),
            folder_id=folder_id,
            order=order,
        )
        return await self._repo.create(stage)
