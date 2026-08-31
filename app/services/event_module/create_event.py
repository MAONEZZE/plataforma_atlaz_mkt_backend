from datetime import date
from uuid import UUID, uuid4

from app.domain.event_module.event_model import EventDate
from app.domain.event_module.event_repo_interface import EventRepository
from app.domain.shared.utils import now_sp


class CreateEvent:
    def __init__(self, repo: EventRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        title: str,
        event_date: date,
        description: str | None = None,
        client_id: UUID | None = None,
    ) -> EventDate:
        now = now_sp()
        event = EventDate(
            id=uuid4(),
            client_id=client_id,
            title=title,
            date=event_date,
            description=description,
            image_url=None,
            created_at=now,
            updated_at=now,
        )
        return await self._repo.create(event)
