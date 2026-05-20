from uuid import UUID, uuid4

from app.domain.content_module.content_exceptions import ModuleNotFound
from app.domain.content_module.content_model import Module
from app.domain.content_module.content_repo_interface import ModuleRepository


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
    def __init__(self, repo: ModuleRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        module_id: UUID,
        title: str | None,
        description: str | None,
        order: int | None,
    ) -> Module:
        module = await self._repo.get_by_id(module_id)
        if module is None:
            raise ModuleNotFound(f"Módulo {module_id} não encontrado.")
        updated = Module(
            id=module.id,
            track_id=module.track_id,
            title=title if title is not None else module.title,
            description=description if description is not None else module.description,
            order=order if order is not None else module.order,
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
