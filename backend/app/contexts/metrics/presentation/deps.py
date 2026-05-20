from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.contexts.metrics.application.use_cases.update_metric import AtualizarMetrica
from app.contexts.metrics.application.use_cases.create_metric import CriarMetrica
from app.contexts.metrics.application.use_cases.list_metrics import ListarMetricas
from app.contexts.metrics.application.use_cases.get_admin_consolidated import (
    ObterAdminConsolidado,
)
from app.contexts.metrics.application.use_cases.get_dashboard_summary import ObterResumoDashboard
from app.contexts.metrics.application.use_cases.get_dashboard_series import ObterSeriesDashboard
from app.contexts.metrics.infrastructure.repositories import SqlAlchemyMetricRepository
from app.core.db import get_session


def _repo(session: AsyncSession) -> SqlAlchemyMetricRepository:
    return SqlAlchemyMetricRepository(session)


def get_criar_metrica(session: AsyncSession = Depends(get_session)) -> CriarMetrica:
    return CriarMetrica(_repo(session))


def get_atualizar_metrica(session: AsyncSession = Depends(get_session)) -> UpdateMetrica:
    return AtualizarMetrica(_repo(session))


def get_listar_metricas(session: AsyncSession = Depends(get_session)) -> ListarMetricas:
    return ListarMetricas(_repo(session))


def get_resumo_dashboard(session: AsyncSession = Depends(get_session)) -> ObterResumoDashboard:
    return ObterResumoDashboard(_repo(session))


def get_series_dashboard(session: AsyncSession = Depends(get_session)) -> ObterSeriesDashboard:
    return ObterSeriesDashboard(_repo(session))


def get_admin_consolidado(
    session: AsyncSession = Depends(get_session),
) -> ObterAdminConsolidado:
    return ObterAdminConsolidado(_repo(session))
