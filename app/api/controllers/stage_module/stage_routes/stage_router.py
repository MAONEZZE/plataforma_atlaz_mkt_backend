from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.config.dependencies.auth_deps import get_current_user
from app.api.controllers.stage_module.stage_dto.stage_dto import SetDoneIn, UserStageOut
from app.database.shared.db_factory import get_session
from app.database.stage_module.stage_repo import SqlAlchemyStageRepository
from app.domain.auth_module.auth_model import User as AuthUser
from app.domain.shared.base_exceptions import AppException
from app.domain.stage_module.stage_exceptions import StageNotFound
from app.services.stage_module.list_folders import ListFolders
from app.services.stage_module.list_user_stages import ListUserStages
from app.services.stage_module.set_stage_done import SetStageDone

router = APIRouter(tags=["stages"])


def _repo(session: AsyncSession) -> SqlAlchemyStageRepository:
    return SqlAlchemyStageRepository(session)


def _list_user_stages(session: AsyncSession = Depends(get_session)) -> ListUserStages:
    return ListUserStages(_repo(session))


def _list_folders(session: AsyncSession = Depends(get_session)) -> ListFolders:
    return ListFolders(_repo(session))


def _set_stage_done(session: AsyncSession = Depends(get_session)) -> SetStageDone:
    return SetStageDone(_repo(session))


@router.get("/stages/me", response_model=list[UserStageOut])
async def list_my_stages(
    user: AuthUser = Depends(get_current_user),
    use_case: ListUserStages = Depends(_list_user_stages),
    folders_use_case: ListFolders = Depends(_list_folders),
) -> list[UserStageOut]:
    items = await use_case.execute(user.id)
    folders = await folders_use_case.execute()
    folder_titles = {f.id: f.title for f in folders}
    return [
        UserStageOut(
            user_id=us.user_id,
            stage_id=us.stage_id,
            done=us.done,
            updated_at=us.updated_at,
            title=stage.title,
            text=stage.text,
            folder_id=stage.folder_id,
            folder_title=folder_titles.get(stage.folder_id) if stage.folder_id else None,
            order=stage.order,
        )
        for us, stage in items
    ]


@router.patch("/stages/me/{stage_id}", response_model=UserStageOut)
async def set_my_stage_done(
    stage_id: UUID,
    body: SetDoneIn,
    user: AuthUser = Depends(get_current_user),
    use_case: SetStageDone = Depends(_set_stage_done),
) -> UserStageOut:
    try:
        us = await use_case.execute(user.id, stage_id, body.done)
    except StageNotFound as exc:
        raise AppException("STAGE_NOT_FOUND", str(exc), 404) from exc
    return UserStageOut(
        user_id=us.user_id,
        stage_id=us.stage_id,
        done=us.done,
        updated_at=us.updated_at,
    )
