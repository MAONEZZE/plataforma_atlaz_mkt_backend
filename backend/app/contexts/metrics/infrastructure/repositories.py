from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.contexts.metrics.domain.entities import WeeklyMetric, UserMonthlyMetrics
from app.contexts.metrics.infrastructure.models import WeeklyMetricModel, UserMetricModel


def _month_range(year: int, month: int) -> tuple[date, date]:
    start = date(year, month, 1)
    if month == 12:
        end = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end = date(year, month + 1, 1) - timedelta(days=1)
    return start, end


def _from_model(m: WeeklyMetricModel) -> WeeklyMetric:
    return WeeklyMetric(
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


class SqlAlchemyMetricRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, metrica: WeeklyMetric) -> WeeklyMetric:
        model = WeeklyMetricModel(
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

    async def get_by_id(self, metrica_id: UUID) -> WeeklyMetric | None:
        result = await self._session.execute(
            select(WeeklyMetricModel).where(WeeklyMetricModel.id == metrica_id)
        )
        m = result.scalar_one_or_none()
        return _from_model(m) if m else None

    async def por_usuario_e_semana(
        self, usuario_id: UUID, semana_inicio: date
    ) -> WeeklyMetric | None:
        result = await self._session.execute(
            select(WeeklyMetricModel).where(
                WeeklyMetricModel.usuario_id == usuario_id,
                WeeklyMetricModel.semana_inicio == semana_inicio,
            )
        )
        m = result.scalar_one_or_none()
        return _from_model(m) if m else None

    async def list_all(
        self, usuario_id: UUID, mes: str | None, page: int, page_size: int
    ) -> tuple[list[WeeklyMetric], int]:
        conditions = [WeeklyMetricModel.usuario_id == usuario_id]
        if mes:
            year, month = int(mes[:4]), int(mes[5:7])
            start, end = _month_range(year, month)
            conditions.extend(
                [
                    WeeklyMetricModel.semana_inicio >= start,
                    WeeklyMetricModel.semana_inicio <= end,
                ]
            )

        count_result = await self._session.execute(
            select(func.count()).select_from(WeeklyMetricModel).where(*conditions)
        )
        total = count_result.scalar_one()

        result = await self._session.execute(
            select(WeeklyMetricModel)
            .where(*conditions)
            .order_by(WeeklyMetricModel.semana_inicio.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return [_from_model(m) for m in result.scalars()], total

    async def update(self, metrica: WeeklyMetric) -> WeeklyMetric:
        await self._session.execute(
            update(WeeklyMetricModel)
            .where(WeeklyMetricModel.id == metrica.id)
            .values(
                ligacoes_agendadas=metrica.ligacoes_agendadas,
                ligacoes_realizadas=metrica.ligacoes_realizadas,
                reunioes_agendadas=metrica.reunioes_agendadas,
                indicacoes=metrica.indicacoes,
                atualizado_em=metrica.atualizado_em,
            )
        )
        return metrica

    async def por_semanas(self, usuario_id: UUID, semanas: list[date]) -> list[WeeklyMetric]:
        if not semanas:
            return []
        result = await self._session.execute(
            select(WeeklyMetricModel).where(
                WeeklyMetricModel.usuario_id == usuario_id,
                WeeklyMetricModel.semana_inicio.in_(semanas),
            )
        )
        return [_from_model(m) for m in result.scalars()]

    async def somar_por_mes(self, usuario_id: UUID, mes: str) -> dict[str, int]:
        year, month = int(mes[:4]), int(mes[5:7])
        start, end = _month_range(year, month)
        result = await self._session.execute(
            select(
                func.coalesce(func.sum(WeeklyMetricModel.ligacoes_agendadas), 0),
                func.coalesce(func.sum(WeeklyMetricModel.ligacoes_realizadas), 0),
                func.coalesce(func.sum(WeeklyMetricModel.reunioes_agendadas), 0),
                func.coalesce(func.sum(WeeklyMetricModel.indicacoes), 0),
            ).where(
                WeeklyMetricModel.usuario_id == usuario_id,
                WeeklyMetricModel.semana_inicio >= start,
                WeeklyMetricModel.semana_inicio <= end,
            )
        )
        row = result.one()
        return {
            "ligacoes_agendadas": int(row[0]),
            "ligacoes_realizadas": int(row[1]),
            "reunioes_agendadas": int(row[2]),
            "indicacoes": int(row[3]),
        }

    async def listar_clientes_com_metricas_mes(self, mes: str) -> list[UserMonthlyMetrics]:
        year, month = int(mes[:4]), int(mes[5:7])
        start, end = _month_range(year, month)
        result = await self._session.execute(
            select(
                UserMetricModel.id,
                UserMetricModel.nome,
                UserMetricModel.foto_url,
                func.coalesce(func.sum(WeeklyMetricModel.ligacoes_agendadas), 0),
                func.coalesce(func.sum(WeeklyMetricModel.ligacoes_realizadas), 0),
                func.coalesce(func.sum(WeeklyMetricModel.reunioes_agendadas), 0),
                func.coalesce(func.sum(WeeklyMetricModel.indicacoes), 0),
                func.max(WeeklyMetricModel.semana_inicio),
            )
            .select_from(UserMetricModel)
            .outerjoin(
                WeeklyMetricModel,
                and_(
                    WeeklyMetricModel.usuario_id == UserMetricModel.id,
                    WeeklyMetricModel.semana_inicio >= start,
                    WeeklyMetricModel.semana_inicio <= end,
                ),
            )
            .where(
                UserMetricModel.role == "cliente",
                UserMetricModel.inativo.is_(False),
            )
            .group_by(
                UserMetricModel.id,
                UserMetricModel.nome,
                UserMetricModel.foto_url,
            )
            .order_by(UserMetricModel.nome)
        )
        return [
            UserMonthlyMetrics(
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
