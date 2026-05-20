from uuid import UUID

from app.contexts.metrics.application.dtos import MetricaDTO
from app.contexts.metrics.application.use_cases.create_metric import _to_dto
from app.contexts.metrics.domain.repositories import MetricaRepository
from app.shared.application.dtos import PagedResponse


class ListMetrics:
    def __init__(self, repo: MetricaRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        usuario_id: UUID,
        mes: str | None,
        page: int,
        page_size: int,
    ) -> PagedResponse[MetricaDTO]:
        metricas, total = await self._repo.listar(usuario_id, mes, page, page_size)
        return PagedResponse(
            items=[_to_dto(m) for m in metricas],
            page=page,
            page_size=page_size,
            total=total,
        )
