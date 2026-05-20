from uuid import UUID

from app.contexts.metricas.application.dtos import MetricaDTO
from app.contexts.metricas.application.use_cases.criar_metrica import _to_dto
from app.contexts.metricas.domain.repositories import MetricaRepository
from app.shared.application.dtos import PagedResponse


class ListarMetricas:
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
