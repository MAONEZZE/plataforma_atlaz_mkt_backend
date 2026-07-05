from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.api.config.dependencies.auth_deps import get_current_user, require_admin
from app.api.controllers.metrics_module.metrics_dto.metrics_dto import (
    EntryIn,
    EntryOut,
    MetricIn,
    MetricOut,
    MetricPatchIn,
    SheetDTO,
    SheetOut,
)
from app.database.metrics_module.metrics_repo import SqlAlchemyMetricRepository
from app.database.shared.db_factory import get_session
from app.domain.auth_module.auth_model import User as AuthUser
from app.domain.metrics_module.metrics_exceptions import MetricNotFound, MetricNotOwnedByUser
from app.domain.metrics_module.metrics_model import Metric
from app.domain.shared.base_exceptions import AppException
from app.services.metrics_module.create_metric import CreateMetric
from app.services.metrics_module.delete_entry import DeleteEntry
from app.services.metrics_module.delete_metric import DeleteMetric
from app.services.metrics_module.get_sheet import GetSheet
from app.services.metrics_module.list_metrics import ListMetrics
from app.services.metrics_module.update_metric import UpdateMetric
from app.services.metrics_module.upsert_entry import UpsertEntry

# ── Dependency helpers ─────────────────────────────────────────────────────────


def _repo(session: AsyncSession) -> SqlAlchemyMetricRepository:
    return SqlAlchemyMetricRepository(session)


def get_create_metric(session: AsyncSession = Depends(get_session)) -> CreateMetric:
    return CreateMetric(_repo(session))


def get_update_metric(session: AsyncSession = Depends(get_session)) -> UpdateMetric:
    return UpdateMetric(_repo(session))


def get_delete_metric(session: AsyncSession = Depends(get_session)) -> DeleteMetric:
    return DeleteMetric(_repo(session))


def get_list_metrics(session: AsyncSession = Depends(get_session)) -> ListMetrics:
    return ListMetrics(_repo(session))


def get_upsert_entry(session: AsyncSession = Depends(get_session)) -> UpsertEntry:
    return UpsertEntry(_repo(session))


def get_delete_entry(session: AsyncSession = Depends(get_session)) -> DeleteEntry:
    return DeleteEntry(_repo(session))


def get_sheet(session: AsyncSession = Depends(get_session)) -> GetSheet:
    return GetSheet(_repo(session))


# ── Mappers ──────────────────────────────────────────────────────────────────

def _metric_out(m: Metric) -> MetricOut:
    return MetricOut(
        id=m.id,
        user_id=m.user_id,
        name=m.name,
        unit=m.unit,
        order=m.order,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


def _sheet_out(dto: SheetDTO) -> SheetOut:
    return SheetOut(
        month=dto.month,
        columns=[_metric_out(m) for m in dto.columns],
        days=dto.days,
        entries=dto.entries,
    )


# ── Routers ────────────────────────────────────────────────────────────────────

router = APIRouter(tags=["metricas"])
admin_router = APIRouter(tags=["admin-metricas"])


@router.get("/metricas", response_model=list[MetricOut])
async def list_metrics(
    user: AuthUser = Depends(get_current_user),
    use_case: ListMetrics = Depends(get_list_metrics),
) -> list[MetricOut]:
    metrics = await use_case.execute(user.id)
    return [_metric_out(m) for m in metrics]


@router.post("/metricas", response_model=MetricOut, status_code=status.HTTP_201_CREATED)
async def create_metric(
    body: MetricIn,
    user: AuthUser = Depends(get_current_user),
    use_case: CreateMetric = Depends(get_create_metric),
) -> MetricOut:
    metric = await use_case.execute(user_id=user.id, name=body.name, unit=body.unit)
    return _metric_out(metric)


@router.patch("/metricas/{metrica_id}", response_model=MetricOut)
async def update_metric(
    metrica_id: UUID,
    body: MetricPatchIn,
    user: AuthUser = Depends(get_current_user),
    use_case: UpdateMetric = Depends(get_update_metric),
) -> MetricOut:
    try:
        metric = await use_case.execute(
            metric_id=metrica_id,
            requesting_user_id=user.id,
            name=body.name,
            unit=body.unit,
            order=body.order,
        )
    except MetricNotFound as exc:
        raise AppException("METRICA_NOT_FOUND", str(exc), 404) from exc
    except MetricNotOwnedByUser as exc:
        raise AppException("FORBIDDEN", str(exc), 403) from exc
    return _metric_out(metric)


@router.delete("/metricas/{metrica_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_metric(
    metrica_id: UUID,
    user: AuthUser = Depends(get_current_user),
    use_case: DeleteMetric = Depends(get_delete_metric),
) -> None:
    try:
        await use_case.execute(metric_id=metrica_id, requesting_user_id=user.id)
    except MetricNotFound as exc:
        raise AppException("METRICA_NOT_FOUND", str(exc), 404) from exc
    except MetricNotOwnedByUser as exc:
        raise AppException("FORBIDDEN", str(exc), 403) from exc


@router.get("/metricas/planilha", response_model=SheetOut)
async def get_my_sheet(
    user: AuthUser = Depends(get_current_user),
    use_case: GetSheet = Depends(get_sheet),
    mes: str | None = Query(default=None),
) -> SheetOut:
    dto = await use_case.execute(user_id=user.id, month=mes)
    return _sheet_out(dto)


@router.put("/metricas/{metrica_id}/valores/{dia}", response_model=EntryOut)
async def upsert_entry(
    metrica_id: UUID,
    dia: date,
    body: EntryIn,
    user: AuthUser = Depends(get_current_user),
    use_case: UpsertEntry = Depends(get_upsert_entry),
) -> EntryOut:
    try:
        entry = await use_case.execute(
            metric_id=metrica_id, requesting_user_id=user.id, day=dia, value=body.value
        )
    except MetricNotFound as exc:
        raise AppException("METRICA_NOT_FOUND", str(exc), 404) from exc
    except MetricNotOwnedByUser as exc:
        raise AppException("FORBIDDEN", str(exc), 403) from exc
    return EntryOut(
        metric_id=entry.metric_id, day=entry.day, value=entry.value, updated_at=entry.updated_at
    )


@router.delete(
    "/metricas/{metrica_id}/valores/{dia}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_entry(
    metrica_id: UUID,
    dia: date,
    user: AuthUser = Depends(get_current_user),
    use_case: DeleteEntry = Depends(get_delete_entry),
) -> None:
    try:
        await use_case.execute(metric_id=metrica_id, requesting_user_id=user.id, day=dia)
    except MetricNotFound as exc:
        raise AppException("METRICA_NOT_FOUND", str(exc), 404) from exc
    except MetricNotOwnedByUser as exc:
        raise AppException("FORBIDDEN", str(exc), 403) from exc


@admin_router.get(
    "/admin/clients/{user_id}/metricas/planilha", response_model=SheetOut
)
async def admin_get_client_sheet(
    user_id: UUID,
    _admin: AuthUser = Depends(require_admin),
    use_case: GetSheet = Depends(get_sheet),
    mes: str | None = Query(default=None),
) -> SheetOut:
    dto = await use_case.execute(user_id=user_id, month=mes)
    return _sheet_out(dto)
