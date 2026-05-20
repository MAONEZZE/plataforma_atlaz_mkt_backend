from uuid import UUID

from app.contexts.metrics.application.dtos import MetricDTO
from app.contexts.metrics.application.use_cases.create_metric import _to_dto
from app.contexts.metrics.domain.repositories import MetricRepository
from app.shared.application.dtos import PagedResponse


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
