import zoneinfo
from datetime import datetime

from app.api.controllers.metrics_module.metrics_dto.metrics_dto import (
    AdminAggregatesDTO,
    AdminConsolidatedDTO,
    UserMonthlyMetricsDTO,
)
from app.domain.metrics_module.metrics_repo_interface import MetricRepository

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
            meetings_held_total=sum(i.meetings_held for i in all_items),
            calls_made_total=sum(i.calls_made for i in all_items),
            sales_total=sum(i.sales for i in all_items),
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
                    meetings_held=i.meetings_held,
                    calls_made=i.calls_made,
                    sales=i.sales,
                    referrals=i.referrals,
                    last_metric_at=i.last_metric_at,
                )
                for i in page_items
            ],
            page=page,
            page_size=page_size,
            total=total,
        )
