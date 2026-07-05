from uuid import UUID

from app.domain.metrics_module.metrics_model import Metric
from app.domain.metrics_module.metrics_repo_interface import MetricRepository


class ListMetrics:
    def __init__(self, repo: MetricRepository) -> None:
        self._repo = repo

    async def execute(self, user_id: UUID) -> list[Metric]:
        return await self._repo.list_metrics(user_id)
