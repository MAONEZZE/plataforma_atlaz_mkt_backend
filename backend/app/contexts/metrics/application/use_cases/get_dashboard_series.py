import zoneinfo
from datetime import date, datetime, timedelta
from uuid import UUID

from app.contexts.metrics.application.dtos import DashboardSeriesDTO, WeeklySeriesDTO
from app.contexts.metrics.domain.repositories import MetricaRepository
from app.contexts.metrics.domain.rules import normalize_to_monday

_SP = zoneinfo.ZoneInfo("America/Sao_Paulo")


class GetDashboardSeries:
    def __init__(self, repo: MetricaRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        usuario_id: UUID,
        semanas: int = 12,
        today: date | None = None,
    ) -> DashboardSeriesDTO:
        if today is None:
            today = datetime.now(tz=_SP).date()

        monday = normalize_to_monday(today)
        # Oldest-first list of N Mondays ending on monday
        datas = [monday - timedelta(weeks=i) for i in range(semanas - 1, -1, -1)]

        metricas = await self._repo.por_semanas(usuario_id, datas)
        por_semana = {m.semana_inicio: m for m in metricas}

        series = [
            WeeklySeriesDTO(
                semana=d,
                ligacoes_agendadas=por_semana[d].ligacoes_agendadas if d in por_semana else 0,
                ligacoes_realizadas=por_semana[d].ligacoes_realizadas if d in por_semana else 0,
                reunioes_agendadas=por_semana[d].reunioes_agendadas if d in por_semana else 0,
                indicacoes=por_semana[d].indicacoes if d in por_semana else 0,
            )
            for d in datas
        ]
        return DashboardSeriesDTO(series=series)
