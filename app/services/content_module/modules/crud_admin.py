from uuid import UUID, uuid4

from app.domain.content_module.content_exceptions import ModuleNotFound, TrackNotFound
from app.domain.content_module.content_model import Module
from app.domain.content_module.content_repo_interface import ModuleRepository, TrackRepository


class CreateModule:
    def __init__(self, repo: ModuleRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        track_id: UUID,
        title: str,
        description: str | None,
        order: int,
    ) -> Module:
        module = Module(
            id=uuid4(),
            track_id=track_id,
            title=title,
            description=description,
            order=order,
        )
        return await self._repo.create(module)


class UpdateModule:
    def __init__(self, repo: ModuleRepository, track_repo: TrackRepository) -> None:
        self._repo = repo
        self._track_repo = track_repo

    async def execute(
        self,
        module_id: UUID,
        title: str | None,
        description: str | None,
        order: int | None,
        track_id: UUID | None = None,
    ) -> Module:
        module = await self._repo.get_by_id(module_id)
        if module is None:
            raise ModuleNotFound(f"Módulo {module_id} não encontrado.")

        new_track_id = module.track_id
        new_order = order if order is not None else module.order
        if track_id is not None and track_id != module.track_id:
            if await self._track_repo.get_by_id(track_id) is None:
                raise TrackNotFound(f"Trilha {track_id} não encontrada.")
            new_track_id = track_id
            # Sem posição explícita, o módulo entra no fim da trilha de destino.
            if order is None:
                new_order = len(await self._repo.list_by_track(track_id))

        updated = Module(
            id=module.id,
            track_id=new_track_id,
            title=title if title is not None else module.title,
            description=description if description is not None else module.description,
            order=new_order,
        )
        return await self._repo.update(updated)


class DeleteModule:
    def __init__(self, repo: ModuleRepository) -> None:
        self._repo = repo

    async def execute(self, module_id: UUID) -> None:
        module = await self._repo.get_by_id(module_id)
        if module is None:
            raise ModuleNotFound(f"Módulo {module_id} não encontrado.")
        await self._repo.delete(module_id)


class ReorderModules:
    def __init__(self, repo: ModuleRepository) -> None:
        self._repo = repo

    async def execute(self, orders: list[tuple[UUID, int]]) -> None:
        await self._repo.reorder(orders)
