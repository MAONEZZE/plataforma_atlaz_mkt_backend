from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.config.dependencies.auth_deps import require_admin
from app.api.controllers.event_module.event_dto.event_dto import (
    DeletedEventsCountOut,
    EventImageUrlOut,
    EventIn,
    EventOut,
    EventPatchIn,
    ListEventsResponse,
)
from app.database.event_module.event_repo import SqlAlchemyEventRepository
from app.database.shared.db_factory import get_session
from app.database.shared.supabase_client import create_supabase_admin_client
from app.domain.auth_module.auth_model import User as AuthUser
from app.domain.event_module.event_exceptions import EventNotFound
from app.domain.event_module.event_model import EventDate
from app.domain.shared.base_exceptions import AppException
from app.domain.user_module.user_exceptions import InvalidPhoto
from app.services.event_module.create_event import CreateEvent
from app.services.event_module.delete_event import DeleteEvent
from app.services.event_module.delete_events_by_year import DeleteEventsByYear
from app.services.event_module.list_events import ListEvents
from app.services.event_module.supabase_event_image_gateway import (
    SupabaseEventImageGateway,
)
from app.services.event_module.update_event import UpdateEvent
from app.services.event_module.upload_event_image import (
    UploadEventImage,
    UploadEventImageInput,
)

admin_router = APIRouter(prefix="/admin", tags=["admin-events"])


def _event_repo(session: AsyncSession = Depends(get_session)) -> SqlAlchemyEventRepository:
    return SqlAlchemyEventRepository(session)


def _create_event(session: AsyncSession = Depends(get_session)) -> CreateEvent:
    return CreateEvent(_event_repo(session))


def _update_event(session: AsyncSession = Depends(get_session)) -> UpdateEvent:
    return UpdateEvent(_event_repo(session))


def _delete_event(session: AsyncSession = Depends(get_session)) -> DeleteEvent:
    return DeleteEvent(_event_repo(session))


def _delete_events_by_year(session: AsyncSession = Depends(get_session)) -> DeleteEventsByYear:
    return DeleteEventsByYear(_event_repo(session))


def _list_events(session: AsyncSession = Depends(get_session)) -> ListEvents:
    return ListEvents(_event_repo(session))


def _upload_event_image(session: AsyncSession = Depends(get_session)) -> UploadEventImage:
    client = create_supabase_admin_client()
    return UploadEventImage(
        repo=_event_repo(session),
        storage=SupabaseEventImageGateway(client),
    )


def _event_out(event: EventDate) -> EventOut:
    return EventOut(
        id=event.id,
        client_id=event.client_id,
        title=event.title,
        date=event.date,
        description=event.description,
        image_url=event.image_url,
        created_at=event.created_at,
        updated_at=event.updated_at,
    )


@admin_router.post("/events", response_model=EventOut, status_code=status.HTTP_201_CREATED)
async def create_event(
    body: EventIn,
    _admin: AuthUser = Depends(require_admin),
    use_case: CreateEvent = Depends(_create_event),
) -> EventOut:
    event = await use_case.execute(
        title=body.title,
        event_date=body.date,
        description=body.description,
        client_id=body.client_id,
    )
    return _event_out(event)


@admin_router.get("/events", response_model=ListEventsResponse)
async def list_events(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    _admin: AuthUser = Depends(require_admin),
    use_case: ListEvents = Depends(_list_events),
) -> ListEventsResponse:
    items, total = await use_case.execute(page=page, page_size=page_size)
    return ListEventsResponse(
        items=[_event_out(e) for e in items],
        page=page,
        page_size=page_size,
        total=total,
    )


@admin_router.delete("/events", response_model=DeletedEventsCountOut)
async def delete_events_by_year(
    year: int = Query(..., ge=2000, le=2100),
    scope: Literal["general", "clients", "all"] = Query(...),
    _admin: AuthUser = Depends(require_admin),
    use_case: DeleteEventsByYear = Depends(_delete_events_by_year),
) -> DeletedEventsCountOut:
    deleted = await use_case.execute(year=year, scope=scope)
    return DeletedEventsCountOut(deleted=deleted)


@admin_router.patch("/events/{event_id}", response_model=EventOut)
async def update_event(
    event_id: UUID,
    body: EventPatchIn,
    _admin: AuthUser = Depends(require_admin),
    use_case: UpdateEvent = Depends(_update_event),
) -> EventOut:
    try:
        event = await use_case.execute(
            event_id=event_id,
            title=body.title,
            event_date=body.date,
            description=body.description,
            client_id=body.client_id,
        )
    except EventNotFound as exc:
        raise AppException("EVENT_NOT_FOUND", str(exc), 404) from exc
    return _event_out(event)


@admin_router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: UUID,
    _admin: AuthUser = Depends(require_admin),
    use_case: DeleteEvent = Depends(_delete_event),
) -> None:
    try:
        await use_case.execute(event_id)
    except EventNotFound as exc:
        raise AppException("EVENT_NOT_FOUND", str(exc), 404) from exc


@admin_router.post("/events/{event_id}/image", response_model=EventImageUrlOut)
async def upload_event_image(
    event_id: UUID,
    image: UploadFile = File(...),
    _admin: AuthUser = Depends(require_admin),
    use_case: UploadEventImage = Depends(_upload_event_image),
) -> EventImageUrlOut:
    data = await image.read()
    inp = UploadEventImageInput(
        event_id=event_id,
        content_type=image.content_type or "",
        data=data,
    )
    try:
        result = await use_case.execute(inp)
    except InvalidPhoto as exc:
        raise AppException("VALIDATION_ERROR", str(exc), 400) from exc
    except EventNotFound as exc:
        raise AppException("EVENT_NOT_FOUND", str(exc), 404) from exc
    return EventImageUrlOut(image_url=result.image_url)
