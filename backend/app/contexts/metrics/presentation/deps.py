from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.contexts.metrics.application.use_cases.update_metric import UpdateMetric
from app.contexts.metrics.application.use_cases.create_metric import CreateMetric
from app.contexts.metrics.application.use_cases.list_metrics import ListMetrics
from app.contexts.metrics.application.use_cases.get_admin_consolidated import (
    GetAdminConsolidated,
)
from app.contexts.metrics.application.use_cases.get_dashboard_summary import GetDashboardSummary
from app.contexts.metrics.application.use_cases.get_dashboard_series import GetDashboardSeries
from app.contexts.metrics.infrastructure.repositories import SqlAlchemyMetricRepository
from app.core.db import get_session


def _repo(session: AsyncSession) -> SqlAlchemyMetricRepository:
    return SqlAlchemyMetricRepository(session)


def get_create_metric(session: AsyncSession = Depends(get_session)) -> CreateMetric:
    return CreateMetric(_repo(session))


def get_update_metric(session: AsyncSession = Depends(get_session)) -> UpdateMetric:
    return UpdateMetric(_repo(session))


def get_list_metrics(session: AsyncSession = Depends(get_session)) -> ListMetrics:
    return ListMetrics(_repo(session))


def get_dashboard_summary(session: AsyncSession = Depends(get_session)) -> GetDashboardSummary:
    return GetDashboardSummary(_repo(session))


def get_dashboard_series(session: AsyncSession = Depends(get_session)) -> GetDashboardSeries:
    return GetDashboardSeries(_repo(session))


def get_admin_consolidated(
    session: AsyncSession = Depends(get_session),
) -> GetAdminConsolidated:
    return GetAdminConsolidated(_repo(session))
