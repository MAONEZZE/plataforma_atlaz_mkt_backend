from app.domain.event_module.event_model import EventDate
from app.domain.event_module.event_repo_interface import EventRepository


class ListEvents:
    def __init__(self, repo: EventRepository) -> None:
        self._repo = repo

    async def execute(self, page: int, page_size: int) -> tuple[list[EventDate], int]:
        return await self._repo.list_for_admin(page=page, page_size=page_size)
