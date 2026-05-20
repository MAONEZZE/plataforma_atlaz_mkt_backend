import zoneinfo
from datetime import date, datetime, timedelta
from uuid import UUID

from app.contexts.metrics.application.dtos import DashboardSeriesDTO, WeeklySeriesDTO
from app.contexts.metrics.domain.repositories import MetricRepository
from app.contexts.metrics.domain.rules import normalize_to_monday

_SP = zoneinfo.ZoneInfo("America/Sao_Paulo")


class GetDashboardSeries:
    def __init__(self, repo: MetricRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        user_id: UUID,
        semanas: int = 12,
        today: date | None = None,
    ) -> DashboardSeriesDTO:
        if today is None:
            today = datetime.now(tz=_SP).date()

        monday = normalize_to_monday(today)
        # Oldest-first list of N Mondays ending on monday
        dates = [monday - timedelta(weeks=i) for i in range(semanas - 1, -1, -1)]

        metrics = await self._repo.get_by_weeks(user_id, dates)
        by_week = {m.week_start: m for m in metrics}

        series = [
            WeeklySeriesDTO(
                week=d,
                calls_scheduled=by_week[d].calls_scheduled if d in by_week else 0,
                calls_made=by_week[d].calls_made if d in by_week else 0,
                meetings_scheduled=by_week[d].meetings_scheduled if d in by_week else 0,
                referrals=by_week[d].referrals if d in by_week else 0,
            )
            for d in dates
        ]
        return DashboardSeriesDTO(series=series)
