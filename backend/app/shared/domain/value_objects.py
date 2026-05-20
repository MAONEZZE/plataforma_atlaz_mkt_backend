from dataclasses import dataclass
from datetime import date, timedelta

from app.shared.domain.exceptions import DomainError


@dataclass(frozen=True)
class Email:
    value: str

    def __post_init__(self) -> None:
        if "@" not in self.value or len(self.value) < 3:
            raise DomainError("Email inválido.")


@dataclass(frozen=True)
class WeekStart:
    value: date

    def __post_init__(self) -> None:
        if self.value.weekday() != 0:
            raise DomainError("Semana deve começar na segunda-feira.")

    @classmethod
    def from_date(cls, d: date) -> "WeekStart":
        monday = d - timedelta(days=d.weekday())
        return cls(value=monday)
