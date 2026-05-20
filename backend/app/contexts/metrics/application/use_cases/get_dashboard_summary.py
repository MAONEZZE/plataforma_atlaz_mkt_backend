import zoneinfo
from datetime import datetime
from uuid import UUID

from app.contexts.metrics.application.dtos import DeltaDTO, DashboardSummaryDTO
from app.contexts.metrics.domain.repositories import MetricRepository

_SP = zoneinfo.ZoneInfo("America/Sao_Paulo")


def _prev_month(month: str) -> str:
    year, mo = int(month[:4]), int(month[5:7])
    if mo == 1:
        return f"{year - 1:04d}-12"
    return f"{year:04d}-{mo - 1:02d}"


def _delta(current: int, previous: int) -> DeltaDTO:
    if previous == 0:
        return DeltaDTO(value=current, delta_pct=None)
    return DeltaDTO(value=current, delta_pct=round((current - previous) / previous * 100, 1))


class GetDashboardSummary:
    def __init__(self, repo: MetricRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        user_id: UUID,
        month: str | None = None,
    ) -> DashboardSummaryDTO:
        if month is None:
            today_sp = datetime.now(tz=_SP).date()
            month = f"{today_sp.year:04d}-{today_sp.month:02d}"

        atual = await self._repo.sum_by_month(user_id, month)
        anterior = await self._repo.sum_by_month(user_id, _prev_month(month))

        return DashboardSummaryDTO(
            month=month,
            calls_scheduled=_delta(atual["calls_scheduled"], anterior["calls_scheduled"]),
            calls_made=_delta(
                atual["calls_made"], anterior["calls_made"]
            ),
            meetings_scheduled=_delta(atual["meetings_scheduled"], anterior["meetings_scheduled"]),
            referrals=_delta(atual["referrals"], anterior["referrals"]),
        )
