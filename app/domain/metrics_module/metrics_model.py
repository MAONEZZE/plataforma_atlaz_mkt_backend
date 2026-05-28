from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID


@dataclass
class WeeklyMetric:
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
class UserMonthlyMetrics:
    """Aggregated metrics for one user in one month — used by admin dashboard."""

    user_id: UUID
    name: str
    photo_url: str | None
    meetings_held: int
    calls_made: int
    sales: int
    referrals: int
    last_metric_at: date | None
