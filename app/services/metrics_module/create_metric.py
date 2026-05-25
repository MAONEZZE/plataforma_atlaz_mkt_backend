from datetime import date
from uuid import UUID, uuid4

from app.api.controllers.metrics_module.metrics_dto.metrics_dto import MetricDTO
from app.domain.metrics_module.metrics_exceptions import (
    DuplicateMetric,
    FutureWeekNotAllowed,
    MetricOutOfWindow,
)
from app.domain.metrics_module.metrics_model import WeeklyMetric
from app.domain.metrics_module.metrics_repo_interface import MetricRepository
from app.domain.metrics_module.metrics_validator import normalize_to_monday, within_edit_window
from app.domain.shared.utils import now_sp, today_sp


def _to_dto(m: WeeklyMetric) -> MetricDTO:
    return MetricDTO(
        id=m.id,
        user_id=m.user_id,
        week_start=m.week_start,
        calls_scheduled=m.calls_scheduled,
        calls_made=m.calls_made,
        meetings_scheduled=m.meetings_scheduled,
        referrals=m.referrals,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


class CreateMetric:
    def __init__(self, repo: MetricRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        user_id: UUID,
        week_start: date,
        calls_scheduled: int,
        calls_made: int,
        meetings_scheduled: int,
        referrals: int,
        is_admin: bool,
        today: date | None = None,
    ) -> MetricDTO:
        today = today or today_sp()
        semana = normalize_to_monday(week_start)

        if semana > today:
            raise FutureWeekNotAllowed(f"Semana {semana} é futura.")

        if not is_admin and not within_edit_window(semana, today):
            raise MetricOutOfWindow(f"Semana {semana} fora da janela de edição de 28 dias.")

        existing = await self._repo.get_by_user_and_week(user_id, semana)
        if existing is not None:
            raise DuplicateMetric(f"Já existe métrica para a semana {semana}.")

        now = now_sp()
        metrica = WeeklyMetric(
            id=uuid4(),
            user_id=user_id,
            week_start=semana,
            calls_scheduled=calls_scheduled,
            calls_made=calls_made,
            meetings_scheduled=meetings_scheduled,
            referrals=referrals,
            created_at=now,
            updated_at=now,
        )
        created = await self._repo.create(metrica)
        return _to_dto(created)
