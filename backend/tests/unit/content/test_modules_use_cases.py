from uuid import UUID, uuid4

import pytest

from app.contexts.content.application.use_cases.modules.crud_admin import (
    UpdateModule,
    CreateModule,
    DeleteModule,
    ReorderModules,
)
from app.contexts.content.domain.entities import Module
from app.contexts.content.domain.exceptions import ModuleNotFound


class FakeModuleRepo:
    def __init__(self, modules: list[Module] | None = None) -> None:
        self._modules: list[Module] = modules or []
        self.reorder_calls: list[list[tuple[UUID, int]]] = []

    async def get_by_id(self, module_id: UUID) -> Module | None:
        return next((m for m in self._modules if m.id == module_id), None)

    async def create(self, module: Module) -> Module:
        self._modules.append(module)
        return module

    async def update(self, module: Module) -> Module:
        self._modules = [module if m.id == module.id else m for m in self._modules]
        return module

    async def delete(self, module_id: UUID) -> None:
        self._modules = [m for m in self._modules if m.id != module_id]

    async def reorder(self, orders: list[tuple[UUID, int]]) -> None:
        self.reorder_calls.append(orders)


def _make_module(title: str = "Module", order: int = 0) -> Module:
    return Module(id=uuid4(), track_id=uuid4(), title=title, description=None, order=order)


async def test_create_module_ok() -> None:
    repo = FakeModuleRepo()
    use_case = CreateModule(repo)
    track_id = uuid4()
    module = await use_case.execute(track_id, "Intro", None, 0)
    assert module.title == "Intro"
    assert module.track_id == track_id


async def test_update_module_not_found_raises() -> None:
    use_case = UpdateModule(FakeModuleRepo())
    with pytest.raises(ModuleNotFound):
        await use_case.execute(uuid4(), "X", None, None)


async def test_update_module_keeps_unchanged_fields() -> None:
    module = _make_module("Original", 2)
    repo = FakeModuleRepo([module])
    use_case = UpdateModule(repo)
    updated = await use_case.execute(module.id, None, "New desc", None)
    assert updated.title == "Original"
    assert updated.description == "New desc"
    assert updated.order == 2


async def test_delete_module_not_found_raises() -> None:
    use_case = DeleteModule(FakeModuleRepo())
    with pytest.raises(ModuleNotFound):
        await use_case.execute(uuid4())


async def test_delete_module_ok() -> None:
    module = _make_module()
    repo = FakeModuleRepo([module])
    use_case = DeleteModule(repo)
    await use_case.execute(module.id)
    assert repo._modules == []


async def test_reorder_modules_calls_repo() -> None:
    repo = FakeModuleRepo()
    use_case = ReorderModules(repo)
    ids = [(uuid4(), i) for i in range(3)]
    await use_case.execute(ids)
    assert repo.reorder_calls == [ids]
