from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field

# ── Application DTOs ───────────────────────────────────────────────────────────

@dataclass
class MetricDTO:
    id: UUID
    user_id: UUID
    week_start: date
    meetings_held: int
    calls_made: int
    sales: int
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
    meetings_held: DeltaDTO
    calls_made: DeltaDTO
    sales: DeltaDTO
    referrals: DeltaDTO


@dataclass
class WeeklySeriesDTO:
    week: date
    meetings_held: int
    calls_made: int
    sales: int
    referrals: int


@dataclass
class DashboardSeriesDTO:
    series: list[WeeklySeriesDTO]


@dataclass
class UserMonthlyMetricsDTO:
    user_id: UUID
    name: str
    photo_url: str | None
    meetings_held: int
    calls_made: int
    sales: int
    referrals: int
    last_metric_at: date | None


@dataclass
class AdminAggregatesDTO:
    meetings_held_total: int
    calls_made_total: int
    sales_total: int
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


# ── Presentation Schemas ───────────────────────────────────────────────────────

class MetricIn(BaseModel):
    user_id: UUID | None = None
    week_start: date
    meetings_held: int = Field(ge=0)
    calls_made: int = Field(ge=0)
    sales: int = Field(ge=0)
    referrals: int = Field(ge=0)


class MetricPatchIn(BaseModel):
    meetings_held: int | None = Field(default=None, ge=0)
    calls_made: int | None = Field(default=None, ge=0)
    sales: int | None = Field(default=None, ge=0)
    referrals: int | None = Field(default=None, ge=0)


class MetricOut(BaseModel):
    id: UUID
    user_id: UUID
    week_start: date
    meetings_held: int
    calls_made: int
    sales: int
    referrals: int
    created_at: datetime
    updated_at: datetime


class MetricListOut(BaseModel):
    items: list[MetricOut]
    page: int
    page_size: int
    total: int


class DeltaOut(BaseModel):
    value: int
    delta_pct: float | None


class DashboardSummaryOut(BaseModel):
    month: str
    meetings_held: DeltaOut
    calls_made: DeltaOut
    sales: DeltaOut
    referrals: DeltaOut


class WeeklySeriesOut(BaseModel):
    week: date
    meetings_held: int
    calls_made: int
    sales: int
    referrals: int


class DashboardSeriesOut(BaseModel):
    series: list[WeeklySeriesOut]


class UserMonthlyMetricsOut(BaseModel):
    user_id: UUID
    name: str
    photo_url: str | None
    meetings_held: int
    calls_made: int
    sales: int
    referrals: int
    last_metric_at: date | None


class AdminAggregatesOut(BaseModel):
    meetings_held_total: int
    calls_made_total: int
    sales_total: int
    referrals_total: int
    users_with_metric_in_month: int
    users_without_metric_in_month: int


class AdminConsolidatedOut(BaseModel):
    aggregates: AdminAggregatesOut
    items: list[UserMonthlyMetricsOut]
    page: int
    page_size: int
    total: int
