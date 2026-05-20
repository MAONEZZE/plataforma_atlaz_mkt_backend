import zoneinfo
from datetime import datetime

from app.contexts.metricas.application.dtos import (
    AdminConsolidadoDTO,
    AgregadosAdminDTO,
    UsuarioMetricasMesDTO,
)
from app.contexts.metricas.domain.repositories import MetricaRepository

_SP = zoneinfo.ZoneInfo("America/Sao_Paulo")


class ObterAdminConsolidado:
    def __init__(self, repo: MetricaRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        mes: str | None,
        busca: str | None,
        page: int,
        page_size: int,
    ) -> AdminConsolidadoDTO:
        if mes is None:
            today_sp = datetime.now(tz=_SP).date()
            mes = f"{today_sp.year:04d}-{today_sp.month:02d}"

        all_items = await self._repo.listar_clientes_com_metricas_mes(mes)

        if busca:
            bl = busca.lower()
            all_items = [i for i in all_items if bl in i.nome.lower()]

        total = len(all_items)

        agregados = AgregadosAdminDTO(
            ligacoes_agendadas_total=sum(i.ligacoes_agendadas for i in all_items),
            ligacoes_realizadas_total=sum(i.ligacoes_realizadas for i in all_items),
            reunioes_agendadas_total=sum(i.reunioes_agendadas for i in all_items),
            indicacoes_total=sum(i.indicacoes for i in all_items),
            mentorados_com_metrica_no_mes=sum(
                1 for i in all_items if i.ultima_metrica_em is not None
            ),
            mentorados_sem_metrica_no_mes=sum(1 for i in all_items if i.ultima_metrica_em is None),
        )

        offset = (page - 1) * page_size
        page_items = all_items[offset : offset + page_size]

        return AdminConsolidadoDTO(
            agregados=agregados,
            items=[
                UsuarioMetricasMesDTO(
                    usuario_id=i.usuario_id,
                    nome=i.nome,
                    foto_url=i.foto_url,
                    ligacoes_agendadas=i.ligacoes_agendadas,
                    ligacoes_realizadas=i.ligacoes_realizadas,
                    reunioes_agendadas=i.reunioes_agendadas,
                    indicacoes=i.indicacoes,
                    ultima_metrica_em=i.ultima_metrica_em,
                )
                for i in page_items
            ],
            page=page,
            page_size=page_size,
            total=total,
        )
