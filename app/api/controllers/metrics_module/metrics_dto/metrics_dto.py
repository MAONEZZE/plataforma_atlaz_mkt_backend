from dataclasses import dataclass, field
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.metrics_module.metrics_model import Metric

# ── Application DTOs ───────────────────────────────────────────────────────────

@dataclass
class SheetDTO:
    """Spreadsheet for one user in one month: columns × days -> value."""

    month: str
    columns: list[Metric]
    days: list[date]
    # entries[str(metric_id)][str(day iso)] = value
    entries: dict[str, dict[str, int]] = field(default_factory=dict)


# ── Presentation Schemas ───────────────────────────────────────────────────────

class MetricIn(BaseModel):
    name: str = Field(min_length=1)
    unit: str = "qtd"


class MetricPatchIn(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    unit: str | None = None
    order: int | None = None


class MetricOut(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    unit: str
    order: int
    created_at: datetime
    updated_at: datetime


class EntryIn(BaseModel):
    value: int = Field(ge=0)


class EntryOut(BaseModel):
    metric_id: UUID
    day: date
    value: int
    updated_at: datetime


class SheetOut(BaseModel):
    month: str
    columns: list[MetricOut]
    days: list[date]
    entries: dict[str, dict[str, int]]
