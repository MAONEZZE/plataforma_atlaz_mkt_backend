# Merged from: metrics/domain/value_objects.py + metrics/domain/rules.py
from dataclasses import dataclass
from datetime import date, timedelta


def normalize_to_monday(d: date) -> date:
    return d - timedelta(days=d.weekday())


def within_edit_window(week_start: date, today: date) -> bool:
    return (today - week_start).days <= 28 and week_start <= today


@dataclass(frozen=True)
class WeekStart:
    value: date

    @classmethod
    def from_date(cls, d: date) -> "WeekStart":
        return cls(value=normalize_to_monday(d))
