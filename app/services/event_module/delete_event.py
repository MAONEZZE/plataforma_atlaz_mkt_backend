from uuid import UUID

from app.domain.event_module.event_exceptions import EventNotFound
from app.domain.event_module.event_repo_interface import EventRepository


class DeleteEvent:
    def __init__(self, repo: EventRepository) -> None:
        self._repo = repo

    async def execute(self, event_id: UUID) -> None:
        event = await self._repo.get_by_id(event_id)
        if event is None:
            raise EventNotFound(f"Event {event_id} not found.")
        await self._repo.delete(event_id)
