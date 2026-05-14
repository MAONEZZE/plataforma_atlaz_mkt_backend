from dataclasses import replace
from datetime import UTC, date, datetime
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest

from app.contexts.metricas.application.dtos import (
    AdminConsolidadoDTO,
    MetricaDTO,
    ResumoDashboardDTO,
    SeriesDashboardDTO,
)
from app.contexts.metricas.application.use_cases.criar_metrica import CriarMetrica
from app.contexts.metricas.application.use_cases.atualizar_metrica import AtualizarMetrica
from app.contexts.metricas.application.use_cases.listar_metricas import ListarMetricas
from app.contexts.metricas.application.use_cases.obter_resumo_dashboard import ObterResumoDashboard
from app.contexts.metricas.application.use_cases.obter_series_dashboard import ObterSeriesDashboard
from app.contexts.metricas.application.use_cases.obter_admin_consolidado import ObterAdminConsolidado
from app.contexts.metricas.domain.entities import MetricaSemanal, MetricasUsuarioMes
from app.contexts.metricas.domain.exceptions import (
    MetricaDuplicada,
    MetricaForaDaJanela,
    MetricaNaoEncontrada,
    MetricaNaoPertenceAoUsuario,
    SemanaFuturaNaoPermitida,
)


TODAY = date(2026, 5, 14)  # Wednesday
MONDAY = date(2026, 5, 11)  # Monday of current week


def _make_metrica(
    usuario_id: UUID | None = None,
    semana_inicio: date = MONDAY,
) -> MetricaSemanal:
    now = datetime.now(tz=UTC)
    return MetricaSemanal(
        id=uuid4(),
        usuario_id=usuario_id or uuid4(),
        semana_inicio=semana_inicio,
        ligacoes_agendadas=10,
        ligacoes_realizadas=8,
        reunioes_agendadas=3,
        indicacoes=1,
        criado_em=now,
        atualizado_em=now,
    )


def _mock_repo(**kwargs: object) -> AsyncMock:
    repo = AsyncMock()
    for attr, val in kwargs.items():
        if isinstance(val, Exception):
            getattr(repo, attr).side_effect = val
        else:
            getattr(repo, attr).return_value = val
    return repo


# ── CriarMetrica ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_criar_metrica_happy_path() -> None:
    usuario_id = uuid4()
    metrica = _make_metrica(usuario_id=usuario_id)
    repo = _mock_repo(por_usuario_e_semana=None, criar=metrica)
    uc = CriarMetrica(repo)
    result = await uc.execute(
        usuario_id=usuario_id,
        semana_inicio=MONDAY,
        ligacoes_agendadas=10,
        ligacoes_realizadas=8,
        reunioes_agendadas=3,
        indicacoes=1,
        is_admin=False,
        today=TODAY,
    )
    assert isinstance(result, MetricaDTO)
    assert result.semana_inicio == MONDAY


@pytest.mark.asyncio
async def test_criar_metrica_normalizes_to_monday() -> None:
    usuario_id = uuid4()
    wednesday = date(2026, 5, 13)  # Wednesday → should normalize to Monday May 11
    metrica = _make_metrica(usuario_id=usuario_id, semana_inicio=MONDAY)
    repo = _mock_repo(por_usuario_e_semana=None, criar=metrica)
    uc = CriarMetrica(repo)
    result = await uc.execute(
        usuario_id=usuario_id,
        semana_inicio=wednesday,
        ligacoes_agendadas=0,
        ligacoes_realizadas=0,
        reunioes_agendadas=0,
        indicacoes=0,
        is_admin=False,
        today=TODAY,
    )
    assert result.semana_inicio == MONDAY


@pytest.mark.asyncio
async def test_criar_metrica_future_semana_raises() -> None:
    future = date(2026, 5, 18)  # next Monday
    repo = _mock_repo(por_usuario_e_semana=None)
    uc = CriarMetrica(repo)
    with pytest.raises(SemanaFuturaNaoPermitida):
        await uc.execute(
            usuario_id=uuid4(),
            semana_inicio=future,
            ligacoes_agendadas=0,
            ligacoes_realizadas=0,
            reunioes_agendadas=0,
            indicacoes=0,
            is_admin=False,
            today=TODAY,
        )


@pytest.mark.asyncio
async def test_criar_metrica_outside_window_raises_for_cliente() -> None:
    old_semana = date(2026, 4, 13)  # 29 days before TODAY=May 14 → wait, let me check: Apr 13 to May 14 = 31 days, outside 28-day window
    repo = _mock_repo(por_usuario_e_semana=None)
    uc = CriarMetrica(repo)
    with pytest.raises(MetricaForaDaJanela):
        await uc.execute(
            usuario_id=uuid4(),
            semana_inicio=old_semana,
            ligacoes_agendadas=0,
            ligacoes_realizadas=0,
            reunioes_agendadas=0,
            indicacoes=0,
            is_admin=False,
            today=TODAY,
        )


@pytest.mark.asyncio
async def test_criar_metrica_outside_window_allowed_for_admin() -> None:
    old_semana = date(2026, 1, 5)  # very old, admin can still create
    metrica = _make_metrica(semana_inicio=old_semana)
    repo = _mock_repo(por_usuario_e_semana=None, criar=metrica)
    uc = CriarMetrica(repo)
    result = await uc.execute(
        usuario_id=uuid4(),
        semana_inicio=old_semana,
        ligacoes_agendadas=5,
        ligacoes_realizadas=5,
        reunioes_agendadas=1,
        indicacoes=0,
        is_admin=True,
        today=TODAY,
    )
    assert isinstance(result, MetricaDTO)


@pytest.mark.asyncio
async def test_criar_metrica_duplicate_raises() -> None:
    existing = _make_metrica()
    repo = _mock_repo(por_usuario_e_semana=existing)
    uc = CriarMetrica(repo)
    with pytest.raises(MetricaDuplicada):
        await uc.execute(
            usuario_id=existing.usuario_id,
            semana_inicio=MONDAY,
            ligacoes_agendadas=0,
            ligacoes_realizadas=0,
            reunioes_agendadas=0,
            indicacoes=0,
            is_admin=False,
            today=TODAY,
        )


# ── AtualizarMetrica ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_atualizar_metrica_happy_path() -> None:
    usuario_id = uuid4()
    metrica = _make_metrica(usuario_id=usuario_id)
    updated = replace(metrica, ligacoes_agendadas=20)
    repo = _mock_repo(por_id=metrica, atualizar=updated)
    uc = AtualizarMetrica(repo)
    result = await uc.execute(
        metrica_id=metrica.id,
        requesting_user_id=usuario_id,
        is_admin=False,
        ligacoes_agendadas=20,
        today=TODAY,
    )
    assert result.ligacoes_agendadas == 20


@pytest.mark.asyncio
async def test_atualizar_metrica_not_found_raises() -> None:
    repo = _mock_repo(por_id=None)
    uc = AtualizarMetrica(repo)
    with pytest.raises(MetricaNaoEncontrada):
        await uc.execute(
            metrica_id=uuid4(),
            requesting_user_id=uuid4(),
            is_admin=False,
            today=TODAY,
        )


@pytest.mark.asyncio
async def test_atualizar_metrica_wrong_owner_raises() -> None:
    metrica = _make_metrica()
    repo = _mock_repo(por_id=metrica)
    uc = AtualizarMetrica(repo)
    with pytest.raises(MetricaNaoPertenceAoUsuario):
        await uc.execute(
            metrica_id=metrica.id,
            requesting_user_id=uuid4(),  # different user
            is_admin=False,
            today=TODAY,
        )


@pytest.mark.asyncio
async def test_atualizar_metrica_outside_window_raises_for_cliente() -> None:
    old_semana = date(2026, 4, 12)  # outside 28-day window (33 days from May 14)
    usuario_id = uuid4()
    metrica = _make_metrica(usuario_id=usuario_id, semana_inicio=old_semana)
    repo = _mock_repo(por_id=metrica)
    uc = AtualizarMetrica(repo)
    with pytest.raises(MetricaForaDaJanela):
        await uc.execute(
            metrica_id=metrica.id,
            requesting_user_id=usuario_id,
            is_admin=False,
            today=TODAY,
        )


@pytest.mark.asyncio
async def test_atualizar_metrica_outside_window_allowed_for_admin() -> None:
    old_semana = date(2026, 1, 5)
    usuario_id = uuid4()
    metrica = _make_metrica(usuario_id=usuario_id, semana_inicio=old_semana)
    updated = replace(metrica, ligacoes_agendadas=99)
    repo = _mock_repo(por_id=metrica, atualizar=updated)
    uc = AtualizarMetrica(repo)
    result = await uc.execute(
        metrica_id=metrica.id,
        requesting_user_id=uuid4(),  # admin can edit anyone's
        is_admin=True,
        ligacoes_agendadas=99,
        today=TODAY,
    )
    assert result.ligacoes_agendadas == 99


# ── ListarMetricas ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_listar_metricas_returns_paged() -> None:
    usuario_id = uuid4()
    metricas = [_make_metrica(usuario_id=usuario_id) for _ in range(3)]
    repo = _mock_repo(listar=(metricas, 3))
    uc = ListarMetricas(repo)
    result = await uc.execute(
        usuario_id=usuario_id, mes=None, page=1, page_size=20
    )
    assert result.total == 3
    assert len(result.items) == 3
    assert all(isinstance(i, MetricaDTO) for i in result.items)
