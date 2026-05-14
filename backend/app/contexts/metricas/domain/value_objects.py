from dataclasses import dataclass
from datetime import date

from app.contexts.metricas.domain.rules import normalize_to_monday


@dataclass(frozen=True)
class SemanaInicio:
    value: date

    @classmethod
    def from_date(cls, d: date) -> "SemanaInicio":
        return cls(value=normalize_to_monday(d))
