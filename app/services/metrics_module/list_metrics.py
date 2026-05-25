from uuid import UUID

from app.api.controllers.metrics_module.metrics_dto.metrics_dto import MetricDTO
from app.domain.metrics_module.metrics_repo_interface import MetricRepository
from app.domain.shared.dtos import PagedResponse
from app.services.metrics_module.create_metric import _to_dto


class ListMetrics:
    def __init__(self, repo: MetricRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        user_id: UUID,
        month: str | None,
        page: int,
        page_size: int,
    ) -> PagedResponse[MetricDTO]:
        metrics, total = await self._repo.list_all(user_id, month, page, page_size)
        return PagedResponse(
            items=[_to_dto(m) for m in metrics],
            page=page,
            page_size=page_size,
            total=total,
        )
