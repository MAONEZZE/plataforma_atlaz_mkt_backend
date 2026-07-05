from uuid import UUID

from app.domain.metrics_module.metrics_exceptions import MetricNotFound, MetricNotOwnedByUser
from app.domain.metrics_module.metrics_repo_interface import MetricRepository


class DeleteMetric:
    def __init__(self, repo: MetricRepository) -> None:
        self._repo = repo

    async def execute(self, metric_id: UUID, requesting_user_id: UUID) -> None:
        metric = await self._repo.get_metric_by_id(metric_id)
        if metric is None:
            raise MetricNotFound(f"Métrica {metric_id} não encontrada.")
        if metric.user_id != requesting_user_id:
            raise MetricNotOwnedByUser("Métrica não pertence ao usuário.")
        await self._repo.delete_metric(metric_id)
