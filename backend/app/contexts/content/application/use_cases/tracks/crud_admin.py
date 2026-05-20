from uuid import UUID, uuid4

from app.contexts.content.domain.entities import Track
from app.contexts.content.domain.exceptions import TrackNotFound
from app.contexts.content.domain.repositories import TrilhaRepository
from app.shared.utils import now_sp


class CreateTrack:
    def __init__(self, repo: TrackRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        titulo: str,
        descricao: str | None,
        capa_url: str | None,
        ordem: int,
    ) -> Track:
        trilha = Track(
            id=uuid4(),
            titulo=titulo,
            descricao=descricao,
            capa_url=capa_url,
            ordem=ordem,
            criado_em=now_sp(),
        )
        return await self._repo.create(trilha)


class UpdateTrack:
    def __init__(self, repo: TrackRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        trilha_id: UUID,
        titulo: str | None,
        descricao: str | None,
        capa_url: str | None,
        ordem: int | None,
    ) -> Track:
        trilha = await self._repo.get_by_id(trilha_id)
        if trilha is None:
            raise TrackNotFound(f"Trilha {trilha_id} não encontrada.")
        updated = Track(
            id=trilha.id,
            titulo=titulo if titulo is not None else trilha.titulo,
            descricao=descricao if descricao is not None else trilha.descricao,
            capa_url=capa_url if capa_url is not None else trilha.capa_url,
            ordem=ordem if ordem is not None else trilha.ordem,
            criado_em=trilha.criado_em,
        )
        return await self._repo.update(updated)


class DeleteTrack:
    def __init__(self, repo: TrackRepository) -> None:
        self._repo = repo

    async def execute(self, trilha_id: UUID) -> None:
        trilha = await self._repo.get_by_id(trilha_id)
        if trilha is None:
            raise TrackNotFound(f"Trilha {trilha_id} não encontrada.")
        await self._repo.delete(trilha_id)


class ReorderTracks:
    def __init__(self, repo: TrackRepository) -> None:
        self._repo = repo

    async def execute(self, ordens: list[tuple[UUID, int]]) -> None:
        await self._repo.reorder(ordens)
