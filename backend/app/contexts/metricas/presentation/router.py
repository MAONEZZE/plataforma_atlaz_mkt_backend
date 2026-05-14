from uuid import UUID

from fastapi import APIRouter, Depends, Query
from starlette import status

from app.contexts.auth.domain.entities import Usuario
from app.contexts.metricas.application.use_cases.atualizar_metrica import AtualizarMetrica
from app.contexts.metricas.application.use_cases.criar_metrica import CriarMetrica
from app.contexts.metricas.application.use_cases.listar_metricas import ListarMetricas
from app.contexts.metricas.application.use_cases.obter_admin_consolidado import (
    ObterAdminConsolidado,
)
from app.contexts.metricas.application.use_cases.obter_resumo_dashboard import ObterResumoDashboard
from app.contexts.metricas.application.use_cases.obter_series_dashboard import ObterSeriesDashboard
from app.contexts.metricas.domain.exceptions import (
    MetricaDuplicada,
    MetricaForaDaJanela,
    MetricaNaoEncontrada,
    MetricaNaoPertenceAoUsuario,
    SemanaFuturaNaoPermitida,
)
from app.contexts.metricas.presentation.deps import (
    get_admin_consolidado,
    get_atualizar_metrica,
    get_criar_metrica,
    get_listar_metricas,
    get_resumo_dashboard,
    get_series_dashboard,
)
from app.contexts.metricas.presentation.schemas import (
    AdminConsolidadoOut,
    AgregadosAdminOut,
    DeltaOut,
    MetricaIn,
    MetricaListOut,
    MetricaOut,
    MetricaPatchIn,
    ResumoDashboardOut,
    SeriesDashboardOut,
    SerieSemanalOut,
    UsuarioMetricasMesOut,
)
from app.core.deps import get_current_user, require_admin
from app.core.exceptions import AppException

router = APIRouter(tags=["metricas"])
admin_router = APIRouter(tags=["admin-metricas"])


@router.get("/metricas", response_model=MetricaListOut)
async def listar_metricas(
    user: Usuario = Depends(get_current_user),
    use_case: ListarMetricas = Depends(get_listar_metricas),
    usuario_id: UUID | None = Query(default=None),
    mes: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> MetricaListOut:
    target_id = usuario_id if user.role == "admin" and usuario_id else user.id
    paged = await use_case.execute(target_id, mes, page, page_size)
    return MetricaListOut(
        items=[
            MetricaOut(
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
            for m in paged.items
        ],
        page=paged.page,
        page_size=paged.page_size,
        total=paged.total,
    )


@router.post("/metricas", response_model=MetricaOut, status_code=status.HTTP_201_CREATED)
async def criar_metrica(
    body: MetricaIn,
    user: Usuario = Depends(get_current_user),
    use_case: CriarMetrica = Depends(get_criar_metrica),
) -> MetricaOut:
    is_admin = user.role == "admin"

    if is_admin:
        target_id = body.usuario_id or user.id
    else:
        if body.usuario_id and body.usuario_id != user.id:
            raise AppException("FORBIDDEN", "Não pode criar métrica para outro usuário.", 403)
        target_id = user.id

    try:
        dto = await use_case.execute(
            usuario_id=target_id,
            semana_inicio=body.semana_inicio,
            ligacoes_agendadas=body.ligacoes_agendadas,
            ligacoes_realizadas=body.ligacoes_realizadas,
            reunioes_agendadas=body.reunioes_agendadas,
            indicacoes=body.indicacoes,
            is_admin=is_admin,
        )
    except SemanaFuturaNaoPermitida as exc:
        raise AppException("SEMANA_FUTURA", str(exc), 422) from exc
    except MetricaForaDaJanela as exc:
        raise AppException("FORA_DA_JANELA", str(exc), 422) from exc
    except MetricaDuplicada as exc:
        raise AppException("METRICA_DUPLICADA", str(exc), 409) from exc

    return MetricaOut(
        id=dto.id,
        usuario_id=dto.usuario_id,
        semana_inicio=dto.semana_inicio,
        ligacoes_agendadas=dto.ligacoes_agendadas,
        ligacoes_realizadas=dto.ligacoes_realizadas,
        reunioes_agendadas=dto.reunioes_agendadas,
        indicacoes=dto.indicacoes,
        criado_em=dto.criado_em,
        atualizado_em=dto.atualizado_em,
    )


@router.patch("/metricas/{metrica_id}", response_model=MetricaOut)
async def atualizar_metrica(
    metrica_id: UUID,
    body: MetricaPatchIn,
    user: Usuario = Depends(get_current_user),
    use_case: AtualizarMetrica = Depends(get_atualizar_metrica),
) -> MetricaOut:
    try:
        dto = await use_case.execute(
            metrica_id=metrica_id,
            requesting_user_id=user.id,
            is_admin=user.role == "admin",
            ligacoes_agendadas=body.ligacoes_agendadas,
            ligacoes_realizadas=body.ligacoes_realizadas,
            reunioes_agendadas=body.reunioes_agendadas,
            indicacoes=body.indicacoes,
        )
    except MetricaNaoEncontrada as exc:
        raise AppException("METRICA_NOT_FOUND", str(exc), 404) from exc
    except MetricaNaoPertenceAoUsuario as exc:
        raise AppException("FORBIDDEN", str(exc), 403) from exc
    except MetricaForaDaJanela as exc:
        raise AppException("FORA_DA_JANELA", str(exc), 422) from exc

    return MetricaOut(
        id=dto.id,
        usuario_id=dto.usuario_id,
        semana_inicio=dto.semana_inicio,
        ligacoes_agendadas=dto.ligacoes_agendadas,
        ligacoes_realizadas=dto.ligacoes_realizadas,
        reunioes_agendadas=dto.reunioes_agendadas,
        indicacoes=dto.indicacoes,
        criado_em=dto.criado_em,
        atualizado_em=dto.atualizado_em,
    )


@router.get("/dashboard/resumo", response_model=ResumoDashboardOut)
async def obter_resumo(
    user: Usuario = Depends(get_current_user),
    use_case: ObterResumoDashboard = Depends(get_resumo_dashboard),
    usuario_id: UUID | None = Query(default=None),
    mes: str | None = Query(default=None),
) -> ResumoDashboardOut:
    target_id = usuario_id if user.role == "admin" and usuario_id else user.id
    dto = await use_case.execute(usuario_id=target_id, mes=mes)
    return ResumoDashboardOut(
        mes=dto.mes,
        ligacoes_agendadas=DeltaOut(
            valor=dto.ligacoes_agendadas.valor, delta_pct=dto.ligacoes_agendadas.delta_pct
        ),
        ligacoes_realizadas=DeltaOut(
            valor=dto.ligacoes_realizadas.valor, delta_pct=dto.ligacoes_realizadas.delta_pct
        ),
        reunioes_agendadas=DeltaOut(
            valor=dto.reunioes_agendadas.valor, delta_pct=dto.reunioes_agendadas.delta_pct
        ),
        indicacoes=DeltaOut(
            valor=dto.indicacoes.valor, delta_pct=dto.indicacoes.delta_pct
        ),
    )


@router.get("/dashboard/series", response_model=SeriesDashboardOut)
async def obter_series(
    user: Usuario = Depends(get_current_user),
    use_case: ObterSeriesDashboard = Depends(get_series_dashboard),
    usuario_id: UUID | None = Query(default=None),
    semanas: int = Query(default=12, ge=1, le=52),
) -> SeriesDashboardOut:
    target_id = usuario_id if user.role == "admin" and usuario_id else user.id
    dto = await use_case.execute(usuario_id=target_id, semanas=semanas)
    return SeriesDashboardOut(
        series=[
            SerieSemanalOut(
                semana=s.semana,
                ligacoes_agendadas=s.ligacoes_agendadas,
                ligacoes_realizadas=s.ligacoes_realizadas,
                reunioes_agendadas=s.reunioes_agendadas,
                indicacoes=s.indicacoes,
            )
            for s in dto.series
        ]
    )


@admin_router.get("/admin/dashboard", response_model=AdminConsolidadoOut)
async def admin_dashboard(
    _admin: Usuario = Depends(require_admin),
    use_case: ObterAdminConsolidado = Depends(get_admin_consolidado),
    mes: str | None = Query(default=None),
    busca: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> AdminConsolidadoOut:
    dto = await use_case.execute(mes=mes, busca=busca, page=page, page_size=page_size)
    return AdminConsolidadoOut(
        agregados=AgregadosAdminOut(
            ligacoes_agendadas_total=dto.agregados.ligacoes_agendadas_total,
            ligacoes_realizadas_total=dto.agregados.ligacoes_realizadas_total,
            reunioes_agendadas_total=dto.agregados.reunioes_agendadas_total,
            indicacoes_total=dto.agregados.indicacoes_total,
            mentorados_com_metrica_no_mes=dto.agregados.mentorados_com_metrica_no_mes,
            mentorados_sem_metrica_no_mes=dto.agregados.mentorados_sem_metrica_no_mes,
        ),
        items=[
            UsuarioMetricasMesOut(
                usuario_id=i.usuario_id,
                nome=i.nome,
                foto_url=i.foto_url,
                ligacoes_agendadas=i.ligacoes_agendadas,
                ligacoes_realizadas=i.ligacoes_realizadas,
                reunioes_agendadas=i.reunioes_agendadas,
                indicacoes=i.indicacoes,
                ultima_metrica_em=i.ultima_metrica_em,
            )
            for i in dto.items
        ],
        page=dto.page,
        page_size=dto.page_size,
        total=dto.total,
    )
