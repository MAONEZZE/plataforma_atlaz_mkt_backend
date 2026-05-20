from dataclasses import replace
from datetime import date
from uuid import UUID

from app.contexts.metrics.application.dtos import MetricaDTO
from app.contexts.metrics.application.use_cases.create_metric import _to_dto
from app.contexts.metrics.domain.exceptions import (
    MetricaForaDaJanela,
    MetricNotFound,
    MetricaNaoPertenceAoUsuario,
)
from app.contexts.metrics.domain.repositories import MetricaRepository
from app.contexts.metrics.domain.rules import dentro_janela_edicao
from app.shared.utils import now_sp, today_sp


class UpdateMetric:
    def __init__(self, repo: MetricaRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        metrica_id: UUID,
        requesting_user_id: UUID,
        is_admin: bool,
        ligacoes_agendadas: int | None = None,
        ligacoes_realizadas: int | None = None,
        reunioes_agendadas: int | None = None,
        indicacoes: int | None = None,
        today: date | None = None,
    ) -> MetricaDTO:
        today = today or today_sp()
        metrica = await self._repo.get_by_id(metrica_id)
        if metrica is None:
            raise MetricNotFound(f"Métrica {metrica_id} não encontrada.")

        if not is_admin and metrica.usuario_id != requesting_user_id:
            raise MetricaNaoPertenceAoUsuario("Métrica não pertence ao usuário.")

        if not is_admin and not dentro_janela_edicao(metrica.semana_inicio, today):
            raise MetricaForaDaJanela("Métrica fora da janela de edição de 28 dias.")

        updated = replace(
            metrica,
            ligacoes_agendadas=(
                ligacoes_agendadas
                if ligacoes_agendadas is not None
                else metrica.ligacoes_agendadas
            ),
            ligacoes_realizadas=(
                ligacoes_realizadas
                if ligacoes_realizadas is not None
                else metrica.ligacoes_realizadas
            ),
            reunioes_agendadas=(
                reunioes_agendadas
                if reunioes_agendadas is not None
                else metrica.reunioes_agendadas
            ),
            indicacoes=indicacoes if indicacoes is not None else metrica.indicacoes,
            atualizado_em=now_sp(),
        )
        saved = await self._repo.update(updated)
        return _to_dto(saved)
