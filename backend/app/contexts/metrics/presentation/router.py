from uuid import UUID

from fastapi import APIRouter, Depends, Query
from starlette import status

from app.contexts.auth.domain.entities import User
from app.contexts.metrics.application.use_cases.update_metric import UpdateMetric
from app.contexts.metrics.application.use_cases.create_metric import CreateMetric
from app.contexts.metrics.application.use_cases.list_metrics import ListMetrics
from app.contexts.metrics.application.use_cases.get_admin_consolidated import (
    GetAdminConsolidated,
)
from app.contexts.metrics.application.use_cases.get_dashboard_summary import GetDashboardSummary
from app.contexts.metrics.application.use_cases.get_dashboard_series import GetDashboardSeries
from app.contexts.metrics.domain.exceptions import (
    DuplicateMetric,
    MetricOutOfWindow,
    MetricNotFound,
    MetricNotOwnedByUser,
    FutureWeekNotAllowed,
)
from app.contexts.metrics.presentation.deps import (
    get_admin_consolidated,
    get_update_metric,
    get_create_metric,
    get_list_metrics,
    get_dashboard_summary,
    get_dashboard_series,
)
from app.contexts.metrics.presentation.schemas import (
    AdminConsolidatedOut,
    AdminAggregatesOut,
    DeltaOut,
    MetricIn,
    MetricListOut,
    MetricOut,
    MetricPatchIn,
    DashboardSummaryOut,
    DashboardSeriesOut,
    WeeklySeriesOut,
    UserMonthlyMetricsOut,
)
from app.core.deps import get_current_user, require_admin
from app.core.exceptions import AppException

router = APIRouter(tags=["metricas"])
admin_router = APIRouter(tags=["admin-metricas"])


@router.get("/metricas", response_model=MetricListOut)
async def listar_metricas(
    user: User = Depends(get_current_user),
    use_case: ListMetrics = Depends(get_list_metrics),
    user_id: UUID | None = Query(default=None),
    mes: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> MetricListOut:
    target_id = user_id if user.role == "admin" and user_id else user.id
    paged = await use_case.execute(target_id, mes, page, page_size)
    return MetricListOut(
        items=[
            MetricOut(
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
            for m in paged.items
        ],
        page=paged.page,
        page_size=paged.page_size,
        total=paged.total,
    )


@router.post("/metricas", response_model=MetricOut, status_code=status.HTTP_201_CREATED)
async def criar_metrica(
    body: MetricIn,
    user: User = Depends(get_current_user),
    use_case: CreateMetric = Depends(get_create_metric),
) -> MetricOut:
    is_admin = user.role == "admin"

    if is_admin:
        target_id = body.user_id or user.id
    else:
        if body.user_id and body.user_id != user.id:
            raise AppException("FORBIDDEN", "Não pode criar métrica para outro usuário.", 403)
        target_id = user.id

    try:
        dto = await use_case.execute(
            user_id=target_id,
            week_start=body.week_start,
            calls_scheduled=body.calls_scheduled,
            calls_made=body.calls_made,
            meetings_scheduled=body.meetings_scheduled,
            referrals=body.referrals,
            is_admin=is_admin,
        )
    except FutureWeekNotAllowed as exc:
        raise AppException("SEMANA_FUTURA", str(exc), 422) from exc
    except MetricOutOfWindow as exc:
        raise AppException("FORA_DA_JANELA", str(exc), 422) from exc
    except DuplicateMetric as exc:
        raise AppException("METRICA_DUPLICADA", str(exc), 409) from exc

    return MetricOut(
        id=dto.id,
        user_id=dto.user_id,
        week_start=dto.week_start,
        calls_scheduled=dto.calls_scheduled,
        calls_made=dto.calls_made,
        meetings_scheduled=dto.meetings_scheduled,
        referrals=dto.referrals,
        created_at=dto.created_at,
        updated_at=dto.updated_at,
    )


@router.patch("/metricas/{metrica_id}", response_model=MetricOut)
async def atualizar_metrica(
    metrica_id: UUID,
    body: MetricPatchIn,
    user: User = Depends(get_current_user),
    use_case: UpdateMetric = Depends(get_update_metric),
) -> MetricOut:
    try:
        dto = await use_case.execute(
            metric_id=metrica_id,
            requesting_user_id=user.id,
            is_admin=user.role == "admin",
            calls_scheduled=body.calls_scheduled,
            calls_made=body.calls_made,
            meetings_scheduled=body.meetings_scheduled,
            referrals=body.referrals,
        )
    except MetricNotFound as exc:
        raise AppException("METRICA_NOT_FOUND", str(exc), 404) from exc
    except MetricNotOwnedByUser as exc:
        raise AppException("FORBIDDEN", str(exc), 403) from exc
    except MetricOutOfWindow as exc:
        raise AppException("FORA_DA_JANELA", str(exc), 422) from exc

    return MetricOut(
        id=dto.id,
        user_id=dto.user_id,
        week_start=dto.week_start,
        calls_scheduled=dto.calls_scheduled,
        calls_made=dto.calls_made,
        meetings_scheduled=dto.meetings_scheduled,
        referrals=dto.referrals,
        created_at=dto.created_at,
        updated_at=dto.updated_at,
    )


@router.get("/dashboard/resumo", response_model=DashboardSummaryOut)
async def obter_resumo(
    user: User = Depends(get_current_user),
    use_case: GetDashboardSummary = Depends(get_dashboard_summary),
    user_id: UUID | None = Query(default=None),
    mes: str | None = Query(default=None),
) -> DashboardSummaryOut:
    target_id = user_id if user.role == "admin" and user_id else user.id
    dto = await use_case.execute(user_id=target_id, month=mes)
    return DashboardSummaryOut(
        month=dto.month,
        calls_scheduled=DeltaOut(
            value=dto.calls_scheduled.value, delta_pct=dto.calls_scheduled.delta_pct
        ),
        calls_made=DeltaOut(
            value=dto.calls_made.value, delta_pct=dto.calls_made.delta_pct
        ),
        meetings_scheduled=DeltaOut(
            value=dto.meetings_scheduled.value, delta_pct=dto.meetings_scheduled.delta_pct
        ),
        referrals=DeltaOut(value=dto.referrals.value, delta_pct=dto.referrals.delta_pct),
    )


@router.get("/dashboard/series", response_model=DashboardSeriesOut)
async def obter_series(
    user: User = Depends(get_current_user),
    use_case: GetDashboardSeries = Depends(get_dashboard_series),
    user_id: UUID | None = Query(default=None),
    semanas: int = Query(default=12, ge=1, le=52),
) -> DashboardSeriesOut:
    target_id = user_id if user.role == "admin" and user_id else user.id
    dto = await use_case.execute(user_id=target_id, semanas=semanas)
    return DashboardSeriesOut(
        series=[
            WeeklySeriesOut(
                week=s.week,
                calls_scheduled=s.calls_scheduled,
                calls_made=s.calls_made,
                meetings_scheduled=s.meetings_scheduled,
                referrals=s.referrals,
            )
            for s in dto.series
        ]
    )


@admin_router.get("/admin/dashboard", response_model=AdminConsolidatedOut)
async def admin_dashboard(
    _admin: User = Depends(require_admin),
    use_case: GetAdminConsolidated = Depends(get_admin_consolidated),
    mes: str | None = Query(default=None),
    busca: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> AdminConsolidatedOut:
    dto = await use_case.execute(month=mes, search=busca, page=page, page_size=page_size)
    return AdminConsolidatedOut(
        aggregates=AdminAggregatesOut(
            calls_scheduled_total=dto.aggregates.calls_scheduled_total,
            calls_made_total=dto.aggregates.calls_made_total,
            meetings_scheduled_total=dto.aggregates.meetings_scheduled_total,
            referrals_total=dto.aggregates.referrals_total,
            users_with_metric_in_month=dto.aggregates.users_with_metric_in_month,
            users_without_metric_in_month=dto.aggregates.users_without_metric_in_month,
        ),
        items=[
            UserMonthlyMetricsOut(
                user_id=i.user_id,
                name=i.name,
                photo_url=i.photo_url,
                calls_scheduled=i.calls_scheduled,
                calls_made=i.calls_made,
                meetings_scheduled=i.meetings_scheduled,
                referrals=i.referrals,
                last_metric_at=i.last_metric_at,
            )
            for i in dto.items
        ],
        page=dto.page,
        page_size=dto.page_size,
        total=dto.total,
    )
