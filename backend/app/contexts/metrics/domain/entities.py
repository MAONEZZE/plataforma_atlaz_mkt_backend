from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID


@dataclass
class WeeklyMetric:
    id: UUID
    usuario_id: UUID
    semana_inicio: date
    ligacoes_agendadas: int
    ligacoes_realizadas: int
    reunioes_agendadas: int
    indicacoes: int
    criado_em: datetime
    atualizado_em: datetime


@dataclass
class UserMonthlyMetrics:
    """Aggregated metrics for one user in one month — used by admin dashboard."""

    usuario_id: UUID
    nome: str
    foto_url: str | None
    ligacoes_agendadas: int
    ligacoes_realizadas: int
    reunioes_agendadas: int
    indicacoes: int
    ultima_metrica_em: date | None
