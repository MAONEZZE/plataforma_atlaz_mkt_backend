from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.contexts.metricas.application.use_cases.atualizar_metrica import AtualizarMetrica
from app.contexts.metricas.application.use_cases.criar_metrica import CriarMetrica
from app.contexts.metricas.application.use_cases.listar_metricas import ListarMetricas
from app.contexts.metricas.application.use_cases.obter_admin_consolidado import (
    ObterAdminConsolidado,
)
from app.contexts.metricas.application.use_cases.obter_resumo_dashboard import ObterResumoDashboard
from app.contexts.metricas.application.use_cases.obter_series_dashboard import ObterSeriesDashboard
from app.contexts.metricas.infrastructure.repositories import SqlAlchemyMetricaRepository
from app.core.db import get_session


def _repo(session: AsyncSession) -> SqlAlchemyMetricaRepository:
    return SqlAlchemyMetricaRepository(session)


def get_criar_metrica(session: AsyncSession = Depends(get_session)) -> CriarMetrica:
    return CriarMetrica(_repo(session))


def get_atualizar_metrica(session: AsyncSession = Depends(get_session)) -> AtualizarMetrica:
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
