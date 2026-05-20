from uuid import UUID, uuid4

from app.contexts.content.domain.entities import Track
from app.contexts.content.domain.exceptions import TrackNotFound
from app.contexts.content.domain.repositories import TrackRepository
from app.shared.utils import now_sp


class CreateTrack:
    def __init__(self, repo: TrackRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        title: str,
        description: str | None,
        cover_url: str | None,
        order: int,
    ) -> Track:
        track = Track(
            id=uuid4(),
            title=title,
            description=description,
            cover_url=cover_url,
            order=order,
            created_at=now_sp(),
        )
        return await self._repo.create(track)


class UpdateTrack:
    def __init__(self, repo: TrackRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        track_id: UUID,
        title: str | None,
        description: str | None,
        cover_url: str | None,
        order: int | None,
    ) -> Track:
        track = await self._repo.get_by_id(track_id)
        if track is None:
            raise TrackNotFound(f"Trilha {track_id} não encontrada.")
        updated = Track(
            id=track.id,
            title=title if title is not None else track.title,
            description=description if description is not None else track.description,
            cover_url=cover_url if cover_url is not None else track.cover_url,
            order=order if order is not None else track.order,
            created_at=track.created_at,
        )
        return await self._repo.update(updated)


class DeleteTrack:
    def __init__(self, repo: TrackRepository) -> None:
        self._repo = repo

    async def execute(self, track_id: UUID) -> None:
        track = await self._repo.get_by_id(track_id)
        if track is None:
            raise TrackNotFound(f"Trilha {track_id} não encontrada.")
        await self._repo.delete(track_id)


class ReorderTracks:
    def __init__(self, repo: TrackRepository) -> None:
        self._repo = repo

    async def execute(self, orders: list[tuple[UUID, int]]) -> None:
        await self._repo.reorder(orders)
