from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID


@dataclass
class MetricDTO:
    id: UUID
    user_id: UUID
    week_start: date
    calls_scheduled: int
    calls_made: int
    meetings_scheduled: int
    referrals: int
    created_at: datetime
    updated_at: datetime


@dataclass
class DeltaDTO:
    value: int
    delta_pct: float | None


@dataclass
class DashboardSummaryDTO:
    month: str
    calls_scheduled: DeltaDTO
    calls_made: DeltaDTO
    meetings_scheduled: DeltaDTO
    referrals: DeltaDTO


@dataclass
class WeeklySeriesDTO:
    week: date
    calls_scheduled: int
    calls_made: int
    meetings_scheduled: int
    referrals: int


@dataclass
class DashboardSeriesDTO:
    series: list[WeeklySeriesDTO]


@dataclass
class UserMonthlyMetricsDTO:
    user_id: UUID
    name: str
    photo_url: str | None
    calls_scheduled: int
    calls_made: int
    meetings_scheduled: int
    referrals: int
    last_metric_at: date | None


@dataclass
class AdminAggregatesDTO:
    calls_scheduled_total: int
    calls_made_total: int
    meetings_scheduled_total: int
    referrals_total: int
    users_with_metric_in_month: int
    users_without_metric_in_month: int


@dataclass
class AdminConsolidatedDTO:
    aggregates: AdminAggregatesDTO
    items: list[UserMonthlyMetricsDTO]
    page: int
    page_size: int
    total: int
