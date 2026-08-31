from dataclasses import replace
from datetime import date
from uuid import UUID

from app.domain.event_module.event_exceptions import EventNotFound
from app.domain.event_module.event_model import EventDate
from app.domain.event_module.event_repo_interface import EventRepository
from app.domain.shared.utils import now_sp


class UpdateEvent:
    def __init__(self, repo: EventRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        event_id: UUID,
        title: str | None = None,
        event_date: date | None = None,
        description: str | None = None,
        client_id: UUID | None = None,
    ) -> EventDate:
        event = await self._repo.get_by_id(event_id)
        if event is None:
            raise EventNotFound(f"Event {event_id} not found.")
        updated = replace(
            event,
            title=title if title is not None else event.title,
            date=event_date if event_date is not None else event.date,
            description=description if description is not None else event.description,
            client_id=client_id if client_id is not None else event.client_id,
            updated_at=now_sp(),
        )
        return await self._repo.update(updated)
