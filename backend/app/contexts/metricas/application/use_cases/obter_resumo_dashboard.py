import zoneinfo
from datetime import datetime
from uuid import UUID

from app.contexts.metricas.application.dtos import DeltaDTO, ResumoDashboardDTO
from app.contexts.metricas.domain.repositories import MetricaRepository

_SP = zoneinfo.ZoneInfo("America/Sao_Paulo")


def _prev_mes(mes: str) -> str:
    year, month = int(mes[:4]), int(mes[5:7])
    if month == 1:
        return f"{year - 1:04d}-12"
    return f"{year:04d}-{month - 1:02d}"


def _delta(valor: int, anterior: int) -> DeltaDTO:
    if anterior == 0:
        return DeltaDTO(valor=valor, delta_pct=None)
    return DeltaDTO(valor=valor, delta_pct=round((valor - anterior) / anterior * 100, 1))


class ObterResumoDashboard:
    def __init__(self, repo: MetricaRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        usuario_id: UUID,
        mes: str | None = None,
    ) -> ResumoDashboardDTO:
        if mes is None:
            today_sp = datetime.now(tz=_SP).date()
            mes = f"{today_sp.year:04d}-{today_sp.month:02d}"

        atual = await self._repo.somar_por_mes(usuario_id, mes)
        anterior = await self._repo.somar_por_mes(usuario_id, _prev_mes(mes))

        return ResumoDashboardDTO(
            mes=mes,
            ligacoes_agendadas=_delta(atual["ligacoes_agendadas"], anterior["ligacoes_agendadas"]),
            ligacoes_realizadas=_delta(
                atual["ligacoes_realizadas"], anterior["ligacoes_realizadas"]
            ),
            reunioes_agendadas=_delta(
                atual["reunioes_agendadas"], anterior["reunioes_agendadas"]
            ),
            indicacoes=_delta(atual["indicacoes"], anterior["indicacoes"]),
        )
