from dataclasses import replace
from datetime import date
from uuid import UUID

from app.api.controllers.metrics_module.metrics_dto.metrics_dto import MetricDTO
from app.domain.metrics_module.metrics_exceptions import (
    MetricNotFound,
    MetricNotOwnedByUser,
    MetricOutOfWindow,
)
from app.domain.metrics_module.metrics_repo_interface import MetricRepository
from app.domain.metrics_module.metrics_validator import within_edit_window
from app.domain.shared.utils import now_sp, today_sp
from app.services.metrics_module.metrics_service.create_metric import _to_dto


class UpdateMetric:
    def __init__(self, repo: MetricRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        metric_id: UUID,
        requesting_user_id: UUID,
        is_admin: bool,
        calls_scheduled: int | None = None,
        calls_made: int | None = None,
        meetings_scheduled: int | None = None,
        referrals: int | None = None,
        today: date | None = None,
    ) -> MetricDTO:
        today = today or today_sp()
        metric = await self._repo.get_by_id(metric_id)
        if metric is None:
            raise MetricNotFound(f"Métrica {metric_id} não encontrada.")

        if not is_admin and metric.user_id != requesting_user_id:
            raise MetricNotOwnedByUser("Métrica não pertence ao usuário.")

        if not is_admin and not within_edit_window(metric.week_start, today):
            raise MetricOutOfWindow("Métrica fora da janela de edição de 28 dias.")

        updated = replace(
            metric,
            calls_scheduled=(
                calls_scheduled if calls_scheduled is not None else metric.calls_scheduled
            ),
            calls_made=(calls_made if calls_made is not None else metric.calls_made),
            meetings_scheduled=(
                meetings_scheduled if meetings_scheduled is not None else metric.meetings_scheduled
            ),
            referrals=referrals if referrals is not None else metric.referrals,
            updated_at=now_sp(),
        )
        saved = await self._repo.update(updated)
        return _to_dto(saved)
