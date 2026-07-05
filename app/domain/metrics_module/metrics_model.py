from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID


@dataclass
class Metric:
    """A user-defined metric column in the spreadsheet."""

    id: UUID
    user_id: UUID
    name: str
    unit: str
    order: int
    created_at: datetime
    updated_at: datetime


@dataclass
class MetricEntry:
    """A single daily cell: the value of one metric on one day."""

    id: UUID
    metric_id: UUID
    day: date
    value: int
    created_at: datetime
    updated_at: datetime
