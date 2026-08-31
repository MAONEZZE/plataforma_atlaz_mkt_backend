from datetime import date, datetime
from typing import Any, cast
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.database.shared.sqlalchemy_base import Base
from app.domain.event_module.event_model import EventDate


class EventDateModel(Base):
    __tablename__ = "event_dates"
    __table_args__ = {"schema": "ATZ_HUB", "extend_existing": True}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    client_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        sa.ForeignKey("ATZ_HUB.users.id", ondelete="CASCADE"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(sa.Text, nullable=False)
    date: Mapped[date] = mapped_column("event_date", sa.Date, nullable=False)
    description: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)


def _event_from(m: EventDateModel) -> EventDate:
    return EventDate(
        id=m.id,
        client_id=m.client_id,
        title=m.title,
        date=m.date,
        description=m.description,
        image_url=m.image_url,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


class SqlAlchemyEventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, event: EventDate) -> EventDate:
        model = EventDateModel(
            id=event.id,
            client_id=event.client_id,
            title=event.title,
            date=event.date,
            description=event.description,
            image_url=event.image_url,
            created_at=event.created_at,
            updated_at=event.updated_at,
        )
        self._session.add(model)
        await self._session.flush()
        return event

    async def update(self, event: EventDate) -> EventDate:
        await self._session.execute(
            sa.update(EventDateModel)
            .where(EventDateModel.id == event.id)
            .values(
                client_id=event.client_id,
                title=event.title,
                date=event.date,
                description=event.description,
                image_url=event.image_url,
                updated_at=event.updated_at,
            )
        )
        return event

    async def delete(self, event_id: UUID) -> None:
        await self._session.execute(
            sa.delete(EventDateModel).where(EventDateModel.id == event_id)
        )

    async def get_by_id(self, event_id: UUID) -> EventDate | None:
        result = await self._session.execute(
            sa.select(EventDateModel).where(EventDateModel.id == event_id)
        )
        m = result.scalar_one_or_none()
        return _event_from(m) if m else None

    async def list_for_admin(
        self, page: int, page_size: int
    ) -> tuple[list[EventDate], int]:
        offset = (page - 1) * page_size
        rows = await self._session.execute(
            sa.select(EventDateModel)
            .order_by(EventDateModel.date.asc(), EventDateModel.id)
            .limit(page_size)
            .offset(offset)
        )
        items = [_event_from(m) for m in rows.scalars()]

        total_res = await self._session.execute(
            sa.select(sa.func.count()).select_from(EventDateModel)
        )
        total = int(total_res.scalar_one())
        return items, total

    async def list_for_client(
        self, client_id: UUID, page: int, page_size: int
    ) -> tuple[list[EventDate], int]:
        offset = (page - 1) * page_size
        base_filter = sa.or_(
            EventDateModel.client_id.is_(None),
            EventDateModel.client_id == client_id,
        )

        rows = await self._session.execute(
            sa.select(EventDateModel)
            .where(base_filter)
            .order_by(EventDateModel.date.asc(), EventDateModel.id)
            .limit(page_size)
            .offset(offset)
        )
        items = [_event_from(m) for m in rows.scalars()]

        total_res = await self._session.execute(
            sa.select(sa.func.count()).select_from(EventDateModel).where(base_filter)
        )
        total = int(total_res.scalar_one())
        return items, total

    async def list_for_client_only(self, client_id: UUID) -> list[EventDate]:
        result = await self._session.execute(
            sa.select(EventDateModel)
            .where(EventDateModel.client_id == client_id)
            .order_by(EventDateModel.date.asc(), EventDateModel.id)
        )
        return [_event_from(m) for m in result.scalars()]

    async def delete_by_year(self, year: int, scope: str) -> int:
        year_filter = (EventDateModel.date >= date(year, 1, 1)) & (
            EventDateModel.date < date(year + 1, 1, 1)
        )
        if scope == "general":
            condition = year_filter & EventDateModel.client_id.is_(None)
        elif scope == "clients":
            condition = year_filter & EventDateModel.client_id.is_not(None)
        else:
            condition = year_filter

        result = await self._session.execute(sa.delete(EventDateModel).where(condition))
        return int(cast("sa.CursorResult[Any]", result).rowcount)
