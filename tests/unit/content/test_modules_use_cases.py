from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from app.domain.content_module.content_exceptions import ModuleNotFound, TrackNotFound
from app.domain.content_module.content_model import Module, Track
from app.services.content_module.modules.crud_admin import (
    CreateModule,
    DeleteModule,
    ReorderModules,
    UpdateModule,
)


class FakeModuleRepo:
    def __init__(self, modules: list[Module] | None = None) -> None:
        self._modules: list[Module] = modules or []
        self.reorder_calls: list[list[tuple[UUID, int]]] = []

    async def list_by_track(self, track_id: UUID) -> list[Module]:
        return [m for m in self._modules if m.track_id == track_id]

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


class FakeTrackRepo:
    def __init__(self, tracks: list[Track] | None = None) -> None:
        self._tracks: list[Track] = tracks or []

    async def get_by_id(self, track_id: UUID) -> Track | None:
        return next((t for t in self._tracks if t.id == track_id), None)


def _make_module(
    title: str = "Module", order: int = 0, track_id: UUID | None = None
) -> Module:
    return Module(
        id=uuid4(),
        track_id=track_id or uuid4(),
        title=title,
        description=None,
        order=order,
    )


def _make_track() -> Track:
    return Track(
        id=uuid4(), title="Track", description=None, cover_url=None, order=0,
        created_at=datetime.now(tz=UTC),
    )


async def test_create_module_ok() -> None:
    repo = FakeModuleRepo()
    use_case = CreateModule(repo)
    track_id = uuid4()
    module = await use_case.execute(track_id, "Intro", None, 0)
    assert module.title == "Intro"
    assert module.track_id == track_id


async def test_update_module_not_found_raises() -> None:
    use_case = UpdateModule(FakeModuleRepo(), FakeTrackRepo())
    with pytest.raises(ModuleNotFound):
        await use_case.execute(uuid4(), "X", None, None)


async def test_update_module_keeps_unchanged_fields() -> None:
    module = _make_module("Original", 2)
    repo = FakeModuleRepo([module])
    use_case = UpdateModule(repo, FakeTrackRepo())
    updated = await use_case.execute(module.id, None, "New desc", None)
    assert updated.title == "Original"
    assert updated.description == "New desc"
    assert updated.order == 2
    assert updated.track_id == module.track_id


async def test_update_module_moves_to_other_track_appending_at_end() -> None:
    target = _make_track()
    module = _make_module("Movido", 5)
    existing = [_make_module("Ja la", i, target.id) for i in range(2)]
    repo = FakeModuleRepo([module, *existing])
    use_case = UpdateModule(repo, FakeTrackRepo([target]))

    updated = await use_case.execute(module.id, None, None, None, target.id)

    assert updated.track_id == target.id
    assert updated.order == 2


async def test_update_module_move_respects_explicit_order() -> None:
    target = _make_track()
    module = _make_module("Movido", 5)
    repo = FakeModuleRepo([module, _make_module("Ja la", 0, target.id)])
    use_case = UpdateModule(repo, FakeTrackRepo([target]))

    updated = await use_case.execute(module.id, None, None, 0, target.id)

    assert updated.track_id == target.id
    assert updated.order == 0


async def test_update_module_unknown_track_raises() -> None:
    module = _make_module()
    use_case = UpdateModule(FakeModuleRepo([module]), FakeTrackRepo())
    with pytest.raises(TrackNotFound):
        await use_case.execute(module.id, None, None, None, uuid4())


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
