from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Date,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    delete,
    select,
    update,
)
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.database.shared.sqlalchemy_base import Base
from app.domain.metrics_module.metrics_model import Metric, MetricEntry
from app.domain.shared.utils import now_sp


class MetricModel(Base):
    __tablename__ = "metrics"
    __table_args__ = {"schema": "ATZ_HUB", "extend_existing": True}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("ATZ_HUB.users.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    unit: Mapped[str] = mapped_column(String, nullable=False, default="qtd")
    order: Mapped[int] = mapped_column("sort_order", Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)


class MetricEntryModel(Base):
    __tablename__ = "metric_entries"
    __table_args__ = (
        UniqueConstraint("metric_id", "day"),
        {"schema": "ATZ_HUB", "extend_existing": True},
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    metric_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("ATZ_HUB.metrics.id", ondelete="CASCADE"),
        nullable=False,
    )
    day: Mapped[date] = mapped_column(Date, nullable=False)
    value: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)


def _metric_from(m: MetricModel) -> Metric:
    return Metric(
        id=m.id,
        user_id=m.user_id,
        name=m.name,
        unit=m.unit,
        order=m.order,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


def _entry_from(m: MetricEntryModel) -> MetricEntry:
    return MetricEntry(
        id=m.id,
        metric_id=m.metric_id,
        day=m.day,
        value=m.value,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


class SqlAlchemyMetricRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── metric columns ─────────────────────────────────────────────────────

    async def create_metric(self, metric: Metric) -> Metric:
        model = MetricModel(
            id=metric.id,
            user_id=metric.user_id,
            name=metric.name,
            unit=metric.unit,
            order=metric.order,
            created_at=metric.created_at,
            updated_at=metric.updated_at,
        )
        self._session.add(model)
        await self._session.flush()
        return metric

    async def update_metric(self, metric: Metric) -> Metric:
        await self._session.execute(
            update(MetricModel)
            .where(MetricModel.id == metric.id)
            .values(
                name=metric.name,
                unit=metric.unit,
                order=metric.order,
                updated_at=metric.updated_at,
            ),
            execution_options={"synchronize_session": False},
        )
        return metric

    async def delete_metric(self, metric_id: UUID) -> None:
        await self._session.execute(delete(MetricModel).where(MetricModel.id == metric_id))

    async def get_metric_by_id(self, metric_id: UUID) -> Metric | None:
        result = await self._session.execute(
            select(MetricModel).where(MetricModel.id == metric_id)
        )
        m = result.scalar_one_or_none()
        return _metric_from(m) if m else None

    async def list_metrics(self, user_id: UUID) -> list[Metric]:
        result = await self._session.execute(
            select(MetricModel)
            .where(MetricModel.user_id == user_id)
            .order_by(MetricModel.order, MetricModel.created_at)
        )
        return [_metric_from(m) for m in result.scalars()]

    # ── daily cells ──────────────────────────────────────────────────────────

    async def upsert_entry(self, metric_id: UUID, day: date, value: int) -> MetricEntry:
        now = now_sp()
        stmt = (
            pg_insert(MetricEntryModel)
            .values(
                id=uuid4(),
                metric_id=metric_id,
                day=day,
                value=value,
                created_at=now,
                updated_at=now,
            )
            .on_conflict_do_update(
                index_elements=[MetricEntryModel.metric_id, MetricEntryModel.day],
                set_={"value": value, "updated_at": now},
            )
            .returning(MetricEntryModel)
        )
        result = await self._session.execute(stmt)
        return _entry_from(result.scalar_one())

    async def delete_entry(self, metric_id: UUID, day: date) -> None:
        await self._session.execute(
            delete(MetricEntryModel).where(
                MetricEntryModel.metric_id == metric_id,
                MetricEntryModel.day == day,
            )
        )

    async def list_entries(self, user_id: UUID, start: date, end: date) -> list[MetricEntry]:
        result = await self._session.execute(
            select(MetricEntryModel)
            .join(MetricModel, MetricEntryModel.metric_id == MetricModel.id)
            .where(
                MetricModel.user_id == user_id,
                MetricEntryModel.day >= start,
                MetricEntryModel.day <= end,
            )
        )
        return [_entry_from(m) for m in result.scalars()]
