from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.contexts.metricas.domain.entities import MetricaSemanal, MetricasUsuarioMes
from app.contexts.metricas.infrastructure.models import MetricaSemanalModel, UsuarioMetricaModel


def _month_range(year: int, month: int) -> tuple[date, date]:
    start = date(year, month, 1)
    if month == 12:
        end = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end = date(year, month + 1, 1) - timedelta(days=1)
    return start, end


def _from_model(m: MetricaSemanalModel) -> MetricaSemanal:
    return MetricaSemanal(
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


class SqlAlchemyMetricaRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def criar(self, metrica: MetricaSemanal) -> MetricaSemanal:
        model = MetricaSemanalModel(
            id=metrica.id,
            usuario_id=metrica.usuario_id,
            semana_inicio=metrica.semana_inicio,
            ligacoes_agendadas=metrica.ligacoes_agendadas,
            ligacoes_realizadas=metrica.ligacoes_realizadas,
            reunioes_agendadas=metrica.reunioes_agendadas,
            indicacoes=metrica.indicacoes,
            criado_em=metrica.criado_em,
            atualizado_em=metrica.atualizado_em,
        )
        self._session.add(model)
        await self._session.flush()
        return metrica

    async def por_id(self, metrica_id: UUID) -> MetricaSemanal | None:
        result = await self._session.execute(
            select(MetricaSemanalModel).where(MetricaSemanalModel.id == metrica_id)
        )
        m = result.scalar_one_or_none()
        return _from_model(m) if m else None

    async def por_usuario_e_semana(
        self, usuario_id: UUID, semana_inicio: date
    ) -> MetricaSemanal | None:
        result = await self._session.execute(
            select(MetricaSemanalModel).where(
                MetricaSemanalModel.usuario_id == usuario_id,
                MetricaSemanalModel.semana_inicio == semana_inicio,
            )
        )
        m = result.scalar_one_or_none()
        return _from_model(m) if m else None

    async def listar(
        self, usuario_id: UUID, mes: str | None, page: int, page_size: int
    ) -> tuple[list[MetricaSemanal], int]:
        conditions = [MetricaSemanalModel.usuario_id == usuario_id]
        if mes:
            year, month = int(mes[:4]), int(mes[5:7])
            start, end = _month_range(year, month)
            conditions.extend(
                [
                    MetricaSemanalModel.semana_inicio >= start,
                    MetricaSemanalModel.semana_inicio <= end,
                ]
            )

        count_result = await self._session.execute(
            select(func.count())
            .select_from(MetricaSemanalModel)
            .where(*conditions)
        )
        total = count_result.scalar_one()

        result = await self._session.execute(
            select(MetricaSemanalModel)
            .where(*conditions)
            .order_by(MetricaSemanalModel.semana_inicio.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return [_from_model(m) for m in result.scalars()], total

    async def atualizar(self, metrica: MetricaSemanal) -> MetricaSemanal:
        await self._session.execute(
            update(MetricaSemanalModel)
            .where(MetricaSemanalModel.id == metrica.id)
            .values(
                ligacoes_agendadas=metrica.ligacoes_agendadas,
                ligacoes_realizadas=metrica.ligacoes_realizadas,
                reunioes_agendadas=metrica.reunioes_agendadas,
                indicacoes=metrica.indicacoes,
                atualizado_em=metrica.atualizado_em,
            )
        )
        return metrica

    async def por_semanas(
        self, usuario_id: UUID, semanas: list[date]
    ) -> list[MetricaSemanal]:
        if not semanas:
            return []
        result = await self._session.execute(
            select(MetricaSemanalModel).where(
                MetricaSemanalModel.usuario_id == usuario_id,
                MetricaSemanalModel.semana_inicio.in_(semanas),
            )
        )
        return [_from_model(m) for m in result.scalars()]

    async def somar_por_mes(self, usuario_id: UUID, mes: str) -> dict[str, int]:
        year, month = int(mes[:4]), int(mes[5:7])
        start, end = _month_range(year, month)
        result = await self._session.execute(
            select(
                func.coalesce(func.sum(MetricaSemanalModel.ligacoes_agendadas), 0),
                func.coalesce(func.sum(MetricaSemanalModel.ligacoes_realizadas), 0),
                func.coalesce(func.sum(MetricaSemanalModel.reunioes_agendadas), 0),
                func.coalesce(func.sum(MetricaSemanalModel.indicacoes), 0),
            ).where(
                MetricaSemanalModel.usuario_id == usuario_id,
                MetricaSemanalModel.semana_inicio >= start,
                MetricaSemanalModel.semana_inicio <= end,
            )
        )
        row = result.one()
        return {
            "ligacoes_agendadas": int(row[0]),
            "ligacoes_realizadas": int(row[1]),
            "reunioes_agendadas": int(row[2]),
            "indicacoes": int(row[3]),
        }

    async def listar_clientes_com_metricas_mes(
        self, mes: str
    ) -> list[MetricasUsuarioMes]:
        year, month = int(mes[:4]), int(mes[5:7])
        start, end = _month_range(year, month)
        result = await self._session.execute(
            select(
                UsuarioMetricaModel.id,
                UsuarioMetricaModel.nome,
                UsuarioMetricaModel.foto_url,
                func.coalesce(func.sum(MetricaSemanalModel.ligacoes_agendadas), 0),
                func.coalesce(func.sum(MetricaSemanalModel.ligacoes_realizadas), 0),
                func.coalesce(func.sum(MetricaSemanalModel.reunioes_agendadas), 0),
                func.coalesce(func.sum(MetricaSemanalModel.indicacoes), 0),
                func.max(MetricaSemanalModel.semana_inicio),
            )
            .select_from(UsuarioMetricaModel)
            .outerjoin(
                MetricaSemanalModel,
                and_(
                    MetricaSemanalModel.usuario_id == UsuarioMetricaModel.id,
                    MetricaSemanalModel.semana_inicio >= start,
                    MetricaSemanalModel.semana_inicio <= end,
                ),
            )
            .where(
                UsuarioMetricaModel.role == "cliente",
                UsuarioMetricaModel.inativo.is_(False),
            )
            .group_by(
                UsuarioMetricaModel.id,
                UsuarioMetricaModel.nome,
                UsuarioMetricaModel.foto_url,
            )
            .order_by(UsuarioMetricaModel.nome)
        )
        return [
            MetricasUsuarioMes(
                usuario_id=row[0],
                nome=row[1],
                foto_url=row[2],
                ligacoes_agendadas=int(row[3]),
                ligacoes_realizadas=int(row[4]),
                reunioes_agendadas=int(row[5]),
                indicacoes=int(row[6]),
                ultima_metrica_em=row[7],
            )
            for row in result.all()
        ]
