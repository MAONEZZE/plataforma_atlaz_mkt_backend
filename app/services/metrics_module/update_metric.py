from dataclasses import replace
from uuid import UUID

from app.domain.metrics_module.metrics_exceptions import MetricNotFound, MetricNotOwnedByUser
from app.domain.metrics_module.metrics_model import Metric
from app.domain.metrics_module.metrics_repo_interface import MetricRepository
from app.domain.shared.utils import now_sp


class UpdateMetric:
    def __init__(self, repo: MetricRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        metric_id: UUID,
        requesting_user_id: UUID,
        name: str | None = None,
        unit: str | None = None,
        order: int | None = None,
    ) -> Metric:
        metric = await self._repo.get_metric_by_id(metric_id)
        if metric is None:
            raise MetricNotFound(f"Métrica {metric_id} não encontrada.")
        if metric.user_id != requesting_user_id:
            raise MetricNotOwnedByUser("Métrica não pertence ao usuário.")

        updated = replace(
            metric,
            name=name if name is not None else metric.name,
            unit=unit if unit is not None else metric.unit,
            order=order if order is not None else metric.order,
            updated_at=now_sp(),
        )
        return await self._repo.update_metric(updated)
