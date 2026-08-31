from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.config.dependencies.auth_deps import get_current_user
from app.api.controllers.event_module.event_dto.event_dto import (
    ClientEventOut,
    ListClientEventsResponse,
)
from app.database.event_module.event_repo import SqlAlchemyEventRepository
from app.database.shared.db_factory import get_session
from app.domain.auth_module.auth_model import User as AuthUser
from app.services.event_module.list_client_events import ListClientEvents

router = APIRouter(tags=["events"])


def _list_client_events(session: AsyncSession = Depends(get_session)) -> ListClientEvents:
    return ListClientEvents(SqlAlchemyEventRepository(session))


@router.get("/events", response_model=ListClientEventsResponse)
async def list_events(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    user: AuthUser = Depends(get_current_user),
    use_case: ListClientEvents = Depends(_list_client_events),
) -> ListClientEventsResponse:
    items, total = await use_case.execute(
        client_id=user.id, page=page, page_size=page_size
    )
    return ListClientEventsResponse(
        items=[
            ClientEventOut(
                id=e.id,
                title=e.title,
                date=e.date,
                description=e.description,
                image_url=e.image_url,
                is_global=e.client_id is None,
            )
            for e in items
        ],
        page=page,
        page_size=page_size,
        total=total,
    )
