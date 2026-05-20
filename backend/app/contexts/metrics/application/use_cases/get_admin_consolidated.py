import zoneinfo
from datetime import datetime

from app.contexts.metrics.application.dtos import (
    AdminConsolidatedDTO,
    AdminAggregatesDTO,
    UserMonthlyMetricsDTO,
)
from app.contexts.metrics.domain.repositories import MetricRepository

_SP = zoneinfo.ZoneInfo("America/Sao_Paulo")


class GetAdminConsolidated:
    def __init__(self, repo: MetricRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        month: str | None,
        search: str | None,
        page: int,
        page_size: int,
    ) -> AdminConsolidatedDTO:
        if month is None:
            today_sp = datetime.now(tz=_SP).date()
            month = f"{today_sp.year:04d}-{today_sp.month:02d}"

        all_items = await self._repo.list_clients_with_metrics_month(month)

        if search:
            bl = search.lower()
            all_items = [i for i in all_items if bl in i.name.lower()]

        total = len(all_items)

        aggregates = AdminAggregatesDTO(
            calls_scheduled_total=sum(i.calls_scheduled for i in all_items),
            calls_made_total=sum(i.calls_made for i in all_items),
            meetings_scheduled_total=sum(i.meetings_scheduled for i in all_items),
            referrals_total=sum(i.referrals for i in all_items),
            users_with_metric_in_month=sum(
                1 for i in all_items if i.last_metric_at is not None
            ),
            users_without_metric_in_month=sum(1 for i in all_items if i.last_metric_at is None),
        )

        offset = (page - 1) * page_size
        page_items = all_items[offset : offset + page_size]

        return AdminConsolidatedDTO(
            aggregates=aggregates,
            items=[
                UserMonthlyMetricsDTO(
                    user_id=i.user_id,
                    name=i.name,
                    photo_url=i.photo_url,
                    calls_scheduled=i.calls_scheduled,
                    calls_made=i.calls_made,
                    meetings_scheduled=i.meetings_scheduled,
                    referrals=i.referrals,
                    last_metric_at=i.last_metric_at,
                )
                for i in page_items
            ],
            page=page,
            page_size=page_size,
            total=total,
        )
