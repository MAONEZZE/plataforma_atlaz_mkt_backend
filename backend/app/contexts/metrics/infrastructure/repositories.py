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
        user_id=m.user_id,
        week_start=m.week_start,
        calls_scheduled=m.calls_scheduled,
        calls_made=m.calls_made,
        meetings_scheduled=m.meetings_scheduled,
        referrals=m.referrals,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


class SqlAlchemyMetricRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, metric: WeeklyMetric) -> WeeklyMetric:
        model = WeeklyMetricModel(
            id=metric.id,
            user_id=metric.user_id,
            week_start=metric.week_start,
            calls_scheduled=metric.calls_scheduled,
            calls_made=metric.calls_made,
            meetings_scheduled=metric.meetings_scheduled,
            referrals=metric.referrals,
            created_at=metric.created_at,
            updated_at=metric.updated_at,
        )
        self._session.add(model)
        await self._session.flush()
        return metric

    async def get_by_id(self, metric_id: UUID) -> WeeklyMetric | None:
        result = await self._session.execute(
            select(WeeklyMetricModel).where(WeeklyMetricModel.id == metric_id)
        )
        m = result.scalar_one_or_none()
        return _from_model(m) if m else None

    async def get_by_user_and_week(
        self, user_id: UUID, week_start: date
    ) -> WeeklyMetric | None:
        result = await self._session.execute(
            select(WeeklyMetricModel).where(
                WeeklyMetricModel.user_id == user_id,
                WeeklyMetricModel.week_start == week_start,
            )
        )
        m = result.scalar_one_or_none()
        return _from_model(m) if m else None

    async def list_all(
        self, user_id: UUID, month: str | None, page: int, page_size: int
    ) -> tuple[list[WeeklyMetric], int]:
        conditions = [WeeklyMetricModel.user_id == user_id]
        if month:
            year, mo = int(month[:4]), int(month[5:7])
            start, end = _month_range(year, mo)
            conditions.extend(
                [
                    WeeklyMetricModel.week_start >= start,
                    WeeklyMetricModel.week_start <= end,
                ]
            )

        count_result = await self._session.execute(
            select(func.count()).select_from(WeeklyMetricModel).where(*conditions)
        )
        total = count_result.scalar_one()

        result = await self._session.execute(
            select(WeeklyMetricModel)
            .where(*conditions)
            .order_by(WeeklyMetricModel.week_start.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return [_from_model(m) for m in result.scalars()], total

    async def update(self, metric: WeeklyMetric) -> WeeklyMetric:
        await self._session.execute(
            update(WeeklyMetricModel)
            .where(WeeklyMetricModel.id == metric.id)
            .values(
                calls_scheduled=metric.calls_scheduled,
                calls_made=metric.calls_made,
                meetings_scheduled=metric.meetings_scheduled,
                referrals=metric.referrals,
                updated_at=metric.updated_at,
            )
        )
        return metric

    async def get_by_weeks(self, user_id: UUID, weeks: list[date]) -> list[WeeklyMetric]:
        if not weeks:
            return []
        result = await self._session.execute(
            select(WeeklyMetricModel).where(
                WeeklyMetricModel.user_id == user_id,
                WeeklyMetricModel.week_start.in_(weeks),
            )
        )
        return [_from_model(m) for m in result.scalars()]

    async def sum_by_month(self, user_id: UUID, month: str) -> dict[str, int]:
        year, mo = int(month[:4]), int(month[5:7])
        start, end = _month_range(year, mo)
        result = await self._session.execute(
            select(
                func.coalesce(func.sum(WeeklyMetricModel.calls_scheduled), 0),
                func.coalesce(func.sum(WeeklyMetricModel.calls_made), 0),
                func.coalesce(func.sum(WeeklyMetricModel.meetings_scheduled), 0),
                func.coalesce(func.sum(WeeklyMetricModel.referrals), 0),
            ).where(
                WeeklyMetricModel.user_id == user_id,
                WeeklyMetricModel.week_start >= start,
                WeeklyMetricModel.week_start <= end,
            )
        )
        row = result.one()
        return {
            "calls_scheduled": int(row[0]),
            "calls_made": int(row[1]),
            "meetings_scheduled": int(row[2]),
            "referrals": int(row[3]),
        }

    async def list_clients_with_metrics_month(self, month: str) -> list[UserMonthlyMetrics]:
        year, mo = int(month[:4]), int(month[5:7])
        start, end = _month_range(year, mo)
        result = await self._session.execute(
            select(
                UserMetricModel.id,
                UserMetricModel.name,
                UserMetricModel.photo_url,
                func.coalesce(func.sum(WeeklyMetricModel.calls_scheduled), 0),
                func.coalesce(func.sum(WeeklyMetricModel.calls_made), 0),
                func.coalesce(func.sum(WeeklyMetricModel.meetings_scheduled), 0),
                func.coalesce(func.sum(WeeklyMetricModel.referrals), 0),
                func.max(WeeklyMetricModel.week_start),
            )
            .select_from(UserMetricModel)
            .outerjoin(
                WeeklyMetricModel,
                and_(
                    WeeklyMetricModel.user_id == UserMetricModel.id,
                    WeeklyMetricModel.week_start >= start,
                    WeeklyMetricModel.week_start <= end,
                ),
            )
            .where(
                UserMetricModel.role == "cliente",
                UserMetricModel.inactive.is_(False),
            )
            .group_by(
                UserMetricModel.id,
                UserMetricModel.name,
                UserMetricModel.photo_url,
            )
            .order_by(UserMetricModel.name)
        )
        return [
            UserMonthlyMetrics(
                user_id=row[0],
                name=row[1],
                photo_url=row[2],
                calls_scheduled=int(row[3]),
                calls_made=int(row[4]),
                meetings_scheduled=int(row[5]),
                referrals=int(row[6]),
                last_metric_at=row[7],
            )
            for row in result.all()
        ]
