from app.domain.event_module.event_repo_interface import EventRepository


class DeleteEventsByYear:
    def __init__(self, repo: EventRepository) -> None:
        self._repo = repo

    async def execute(self, year: int, scope: str) -> int:
        return await self._repo.delete_by_year(year=year, scope=scope)
