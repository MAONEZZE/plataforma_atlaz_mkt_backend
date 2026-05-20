# Merged from: contexts/metrics/application/dtos.py + contexts/metrics/presentation/schemas.py
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


# ── Presentation Schemas ───────────────────────────────────────────────────────

class MetricIn(BaseModel):
    user_id: UUID | None = None
    week_start: date
    calls_scheduled: int = Field(ge=0)
    calls_made: int = Field(ge=0)
    meetings_scheduled: int = Field(ge=0)
    referrals: int = Field(ge=0)


class MetricPatchIn(BaseModel):
    calls_scheduled: int | None = Field(default=None, ge=0)
    calls_made: int | None = Field(default=None, ge=0)
    meetings_scheduled: int | None = Field(default=None, ge=0)
    referrals: int | None = Field(default=None, ge=0)


class MetricOut(BaseModel):
    id: UUID
    user_id: UUID
    week_start: date
    calls_scheduled: int
    calls_made: int
    meetings_scheduled: int
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
    calls_scheduled: DeltaOut
    calls_made: DeltaOut
    meetings_scheduled: DeltaOut
    referrals: DeltaOut


class WeeklySeriesOut(BaseModel):
    week: date
    calls_scheduled: int
    calls_made: int
    meetings_scheduled: int
    referrals: int


class DashboardSeriesOut(BaseModel):
    series: list[WeeklySeriesOut]


class UserMonthlyMetricsOut(BaseModel):
    user_id: UUID
    name: str
    photo_url: str | None
    calls_scheduled: int
    calls_made: int
    meetings_scheduled: int
    referrals: int
    last_metric_at: date | None


class AdminAggregatesOut(BaseModel):
    calls_scheduled_total: int
    calls_made_total: int
    meetings_scheduled_total: int
    referrals_total: int
    users_with_metric_in_month: int
    users_without_metric_in_month: int


class AdminConsolidatedOut(BaseModel):
    aggregates: AdminAggregatesOut
    items: list[UserMonthlyMetricsOut]
    page: int
    page_size: int
    total: int
