from uuid import UUID, uuid4

from app.contexts.content.domain.entities import Module
from app.contexts.content.domain.exceptions import ModuleNotFound
from app.contexts.content.domain.repositories import ModuloRepository


class CreateModule:
    def __init__(self, repo: ModuleRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        trilha_id: UUID,
        titulo: str,
        descricao: str | None,
        ordem: int,
    ) -> Module:
        modulo = Module(
            id=uuid4(),
            trilha_id=trilha_id,
            titulo=titulo,
            descricao=descricao,
            ordem=ordem,
        )
        return await self._repo.create(modulo)


class UpdateModule:
    def __init__(self, repo: ModuleRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        modulo_id: UUID,
        titulo: str | None,
        descricao: str | None,
        ordem: int | None,
    ) -> Module:
        modulo = await self._repo.get_by_id(modulo_id)
        if modulo is None:
            raise ModuleNotFound(f"Módulo {modulo_id} não encontrado.")
        updated = Module(
            id=modulo.id,
            trilha_id=modulo.trilha_id,
            titulo=titulo if titulo is not None else modulo.titulo,
            descricao=descricao if descricao is not None else modulo.descricao,
            ordem=ordem if ordem is not None else modulo.ordem,
        )
        return await self._repo.update(updated)


class DeleteModule:
    def __init__(self, repo: ModuleRepository) -> None:
        self._repo = repo

    async def execute(self, modulo_id: UUID) -> None:
        modulo = await self._repo.get_by_id(modulo_id)
        if modulo is None:
            raise ModuleNotFound(f"Módulo {modulo_id} não encontrado.")
        await self._repo.delete(modulo_id)


class ReorderModules:
    def __init__(self, repo: ModuleRepository) -> None:
        self._repo = repo

    async def execute(self, ordens: list[tuple[UUID, int]]) -> None:
        await self._repo.reorder(ordens)
