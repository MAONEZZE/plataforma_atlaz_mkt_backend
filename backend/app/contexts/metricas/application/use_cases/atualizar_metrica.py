from dataclasses import replace
from datetime import UTC, date, datetime
from uuid import UUID

from app.contexts.metricas.application.dtos import MetricaDTO
from app.contexts.metricas.application.use_cases.criar_metrica import _to_dto
from app.contexts.metricas.domain.exceptions import (
    MetricaForaDaJanela,
    MetricaNaoEncontrada,
    MetricaNaoPertenceAoUsuario,
)
from app.contexts.metricas.domain.repositories import MetricaRepository
from app.contexts.metricas.domain.rules import dentro_janela_edicao


class AtualizarMetrica:
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
        today = today or datetime.now(tz=UTC).date()
        metrica = await self._repo.por_id(metrica_id)
        if metrica is None:
            raise MetricaNaoEncontrada(f"Métrica {metrica_id} não encontrada.")

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
            atualizado_em=datetime.now(tz=UTC),
        )
        saved = await self._repo.atualizar(updated)
        return _to_dto(saved)
