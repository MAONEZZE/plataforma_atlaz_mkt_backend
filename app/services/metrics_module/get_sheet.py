from calendar import monthrange
from datetime import date
from uuid import UUID

from app.api.controllers.metrics_module.metrics_dto.metrics_dto import SheetDTO
from app.domain.metrics_module.metrics_repo_interface import MetricRepository
from app.domain.shared.utils import today_sp


def _month_range(month: str | None) -> tuple[str, date, date]:
    if month:
        year, mo = int(month[:4]), int(month[5:7])
    else:
        today = today_sp()
        year, mo = today.year, today.month
    last_day = monthrange(year, mo)[1]
    start = date(year, mo, 1)
    end = date(year, mo, last_day)
    return f"{year:04d}-{mo:02d}", start, end


class GetSheet:
    def __init__(self, repo: MetricRepository) -> None:
        self._repo = repo

    async def execute(self, user_id: UUID, month: str | None = None) -> SheetDTO:
        month_str, start, end = _month_range(month)
        columns = await self._repo.list_metrics(user_id)
        entries = await self._repo.list_entries(user_id, start, end)

        grid: dict[str, dict[str, int]] = {}
        for e in entries:
            grid.setdefault(str(e.metric_id), {})[e.day.isoformat()] = e.value

        days = [date(start.year, start.month, d) for d in range(1, end.day + 1)]
        return SheetDTO(month=month_str, columns=columns, days=days, entries=grid)
