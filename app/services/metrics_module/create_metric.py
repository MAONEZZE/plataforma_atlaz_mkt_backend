from uuid import UUID, uuid4

from app.domain.metrics_module.metrics_model import Metric
from app.domain.metrics_module.metrics_repo_interface import MetricRepository
from app.domain.shared.utils import now_sp


class CreateMetric:
    def __init__(self, repo: MetricRepository) -> None:
        self._repo = repo

    async def execute(self, user_id: UUID, name: str, unit: str = "qtd", order: int = 0) -> Metric:
        now = now_sp()
        metric = Metric(
            id=uuid4(),
            user_id=user_id,
            name=name,
            unit=unit,
            order=order,
            created_at=now,
            updated_at=now,
        )
        return await self._repo.create_metric(metric)
