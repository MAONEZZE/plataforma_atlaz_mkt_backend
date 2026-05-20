from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class MetricaIn(BaseModel):
    usuario_id: UUID | None = None
    semana_inicio: date
    ligacoes_agendadas: int = Field(ge=0)
    ligacoes_realizadas: int = Field(ge=0)
    reunioes_agendadas: int = Field(ge=0)
    indicacoes: int = Field(ge=0)


class MetricaPatchIn(BaseModel):
    ligacoes_agendadas: int | None = Field(default=None, ge=0)
    ligacoes_realizadas: int | None = Field(default=None, ge=0)
    reunioes_agendadas: int | None = Field(default=None, ge=0)
    indicacoes: int | None = Field(default=None, ge=0)


class MetricaOut(BaseModel):
    id: UUID
    usuario_id: UUID
    semana_inicio: date
    ligacoes_agendadas: int
    ligacoes_realizadas: int
    reunioes_agendadas: int
    indicacoes: int
    criado_em: datetime
    atualizado_em: datetime


class MetricaListOut(BaseModel):
    items: list[MetricaOut]
    page: int
    page_size: int
    total: int


class DeltaOut(BaseModel):
    valor: int
    delta_pct: float | None


class ResumoDashboardOut(BaseModel):
    mes: str
    ligacoes_agendadas: DeltaOut
    ligacoes_realizadas: DeltaOut
    reunioes_agendadas: DeltaOut
    indicacoes: DeltaOut


class SerieSemanalOut(BaseModel):
    semana: date
    ligacoes_agendadas: int
    ligacoes_realizadas: int
    reunioes_agendadas: int
    indicacoes: int


class SeriesDashboardOut(BaseModel):
    series: list[SerieSemanalOut]


class UsuarioMetricasMesOut(BaseModel):
    usuario_id: UUID
    nome: str
    foto_url: str | None
    ligacoes_agendadas: int
    ligacoes_realizadas: int
    reunioes_agendadas: int
    indicacoes: int
    ultima_metrica_em: date | None


class AgregadosAdminOut(BaseModel):
    ligacoes_agendadas_total: int
    ligacoes_realizadas_total: int
    reunioes_agendadas_total: int
    indicacoes_total: int
    mentorados_com_metrica_no_mes: int
    mentorados_sem_metrica_no_mes: int


class AdminConsolidadoOut(BaseModel):
    agregados: AgregadosAdminOut
    items: list[UsuarioMetricasMesOut]
    page: int
    page_size: int
    total: int
