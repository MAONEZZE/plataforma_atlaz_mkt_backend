from datetime import date
from uuid import UUID, uuid4

from app.contexts.metricas.application.dtos import MetricaDTO
from app.contexts.metricas.domain.entities import MetricaSemanal
from app.contexts.metricas.domain.exceptions import (
    MetricaDuplicada,
    MetricaForaDaJanela,
    SemanaFuturaNaoPermitida,
)
from app.contexts.metricas.domain.repositories import MetricaRepository
from app.contexts.metricas.domain.rules import dentro_janela_edicao, normalize_to_monday
from app.shared.utils import now_sp, today_sp


def _to_dto(m: MetricaSemanal) -> MetricaDTO:
    return MetricaDTO(
        id=m.id,
        usuario_id=m.usuario_id,
        semana_inicio=m.semana_inicio,
        ligacoes_agendadas=m.ligacoes_agendadas,
        ligacoes_realizadas=m.ligacoes_realizadas,
        reunioes_agendadas=m.reunioes_agendadas,
        indicacoes=m.indicacoes,
        criado_em=m.criado_em,
        atualizado_em=m.atualizado_em,
    )


class CriarMetrica:
    def __init__(self, repo: MetricaRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        usuario_id: UUID,
        semana_inicio: date,
        ligacoes_agendadas: int,
        ligacoes_realizadas: int,
        reunioes_agendadas: int,
        indicacoes: int,
        is_admin: bool,
        today: date | None = None,
    ) -> MetricaDTO:
        today = today or today_sp()
        semana = normalize_to_monday(semana_inicio)

        if semana > today:
            raise SemanaFuturaNaoPermitida(f"Semana {semana} é futura.")

        if not is_admin and not dentro_janela_edicao(semana, today):
            raise MetricaForaDaJanela(f"Semana {semana} fora da janela de edição de 28 dias.")

        existing = await self._repo.por_usuario_e_semana(usuario_id, semana)
        if existing is not None:
            raise MetricaDuplicada(f"Já existe métrica para a semana {semana}.")

        now = now_sp()
        metrica = MetricaSemanal(
            id=uuid4(),
            usuario_id=usuario_id,
            semana_inicio=semana,
            ligacoes_agendadas=ligacoes_agendadas,
            ligacoes_realizadas=ligacoes_realizadas,
            reunioes_agendadas=reunioes_agendadas,
            indicacoes=indicacoes,
            criado_em=now,
            atualizado_em=now,
        )
        created = await self._repo.criar(metrica)
        return _to_dto(created)
