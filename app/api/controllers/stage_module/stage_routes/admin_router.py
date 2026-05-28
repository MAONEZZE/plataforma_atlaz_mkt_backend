from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.config.dependencies.auth_deps import require_admin
from app.api.controllers.stage_module.stage_dto.stage_dto import StageIn, StageOut, UserStageOut
from app.database.shared.db_factory import get_session
from app.database.stage_module.stage_repo import SqlAlchemyStageRepository
from app.domain.auth_module.auth_model import User as AuthUser
from app.domain.shared.base_exceptions import AppException
from app.domain.stage_module.stage_exceptions import StageAlreadyAttached, StageNotFound
from app.services.stage_module.attach_stage import AttachStage
from app.services.stage_module.create_stage import CreateStage
from app.services.stage_module.delete_stage import DeleteStage
from app.services.stage_module.detach_stage import DetachStage
from app.services.stage_module.list_stages import ListStages
from app.services.stage_module.update_stage import UpdateStage

admin_router = APIRouter(prefix="/admin", tags=["admin-stages"])


def _repo(session: AsyncSession) -> SqlAlchemyStageRepository:
    return SqlAlchemyStageRepository(session)


def _create_stage(session: AsyncSession = Depends(get_session)) -> CreateStage:
    return CreateStage(_repo(session))


def _list_stages(session: AsyncSession = Depends(get_session)) -> ListStages:
    return ListStages(_repo(session))


def _update_stage(session: AsyncSession = Depends(get_session)) -> UpdateStage:
    return UpdateStage(_repo(session))


def _delete_stage(session: AsyncSession = Depends(get_session)) -> DeleteStage:
    return DeleteStage(_repo(session))


def _attach_stage(session: AsyncSession = Depends(get_session)) -> AttachStage:
    return AttachStage(_repo(session))


def _detach_stage(session: AsyncSession = Depends(get_session)) -> DetachStage:
    return DetachStage(_repo(session))


@admin_router.post("/stages", response_model=StageOut, status_code=status.HTTP_201_CREATED)
async def create_stage(
    body: StageIn,
    _admin: AuthUser = Depends(require_admin),
    use_case: CreateStage = Depends(_create_stage),
) -> StageOut:
    stage = await use_case.execute(text=body.text)
    return StageOut(id=stage.id, text=stage.text, created_at=stage.created_at)


@admin_router.get("/stages", response_model=list[StageOut])
async def list_stages(
    _admin: AuthUser = Depends(require_admin),
    use_case: ListStages = Depends(_list_stages),
) -> list[StageOut]:
    stages = await use_case.execute()
    return [StageOut(id=s.id, text=s.text, created_at=s.created_at) for s in stages]


@admin_router.patch("/stages/{stage_id}", response_model=StageOut)
async def update_stage(
    stage_id: UUID,
    body: StageIn,
    _admin: AuthUser = Depends(require_admin),
    use_case: UpdateStage = Depends(_update_stage),
) -> StageOut:
    try:
        stage = await use_case.execute(stage_id=stage_id, text=body.text)
    except StageNotFound as exc:
        raise AppException("STAGE_NOT_FOUND", str(exc), 404) from exc
    return StageOut(id=stage.id, text=stage.text, created_at=stage.created_at)


@admin_router.delete("/stages/{stage_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_stage(
    stage_id: UUID,
    _admin: AuthUser = Depends(require_admin),
    use_case: DeleteStage = Depends(_delete_stage),
) -> None:
    try:
        await use_case.execute(stage_id=stage_id)
    except StageNotFound as exc:
        raise AppException("STAGE_NOT_FOUND", str(exc), 404) from exc


@admin_router.post(
    "/clients/{user_id}/stages/{stage_id}",
    response_model=UserStageOut,
    status_code=status.HTTP_201_CREATED,
)
async def attach_stage_to_client(
    user_id: UUID,
    stage_id: UUID,
    _admin: AuthUser = Depends(require_admin),
    use_case: AttachStage = Depends(_attach_stage),
) -> UserStageOut:
    try:
        us = await use_case.execute(user_id=user_id, stage_id=stage_id)
    except StageNotFound as exc:
        raise AppException("STAGE_NOT_FOUND", str(exc), 404) from exc
    except StageAlreadyAttached as exc:
        raise AppException("STAGE_ALREADY_ATTACHED", str(exc), 409) from exc
    return UserStageOut(user_id=us.user_id, stage_id=us.stage_id, done=us.done, updated_at=us.updated_at)


@admin_router.delete(
    "/clients/{user_id}/stages/{stage_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def detach_stage_from_client(
    user_id: UUID,
    stage_id: UUID,
    _admin: AuthUser = Depends(require_admin),
    use_case: DetachStage = Depends(_detach_stage),
) -> None:
    await use_case.execute(user_id=user_id, stage_id=stage_id)
