from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID


@dataclass
class MetricDTO:
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
class DeltaDTO:
    valor: int
    delta_pct: float | None


@dataclass
class DashboardSummaryDTO:
    mes: str
    ligacoes_agendadas: DeltaDTO
    ligacoes_realizadas: DeltaDTO
    reunioes_agendadas: DeltaDTO
    indicacoes: DeltaDTO


@dataclass
class WeeklySeriesDTO:
    semana: date
    ligacoes_agendadas: int
    ligacoes_realizadas: int
    reunioes_agendadas: int
    indicacoes: int


@dataclass
class DashboardSeriesDTO:
    series: list[WeeklySeriesDTO]


@dataclass
class UserMonthlyMetricsDTO:
    usuario_id: UUID
    nome: str
    foto_url: str | None
    ligacoes_agendadas: int
    ligacoes_realizadas: int
    reunioes_agendadas: int
    indicacoes: int
    ultima_metrica_em: date | None


@dataclass
class AdminAggregatesDTO:
    ligacoes_agendadas_total: int
    ligacoes_realizadas_total: int
    reunioes_agendadas_total: int
    indicacoes_total: int
    mentorados_com_metrica_no_mes: int
    mentorados_sem_metrica_no_mes: int


@dataclass
class AdminConsolidatedDTO:
    agregados: AdminAggregatesDTO
    items: list[UsuarioMetricasMesDTO]
    page: int
    page_size: int
    total: int
