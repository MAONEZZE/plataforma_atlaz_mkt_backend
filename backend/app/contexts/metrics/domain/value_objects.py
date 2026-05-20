from dataclasses import dataclass
from datetime import date

from app.contexts.metrics.domain.rules import normalize_to_monday


@dataclass(frozen=True)
class WeekStart:
    value: date

    @classmethod
    def from_date(cls, d: date) -> "WeekStart":
        return cls(value=normalize_to_monday(d))
