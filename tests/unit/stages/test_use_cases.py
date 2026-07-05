from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.domain.stage_module.stage_exceptions import (
    StageAlreadyAttached,
    StageFolderNotFound,
    StageNotFound,
)
from app.domain.stage_module.stage_model import Stage, StageFolder, UserStage
from app.services.stage_module.attach_stage import AttachStage
from app.services.stage_module.create_folder import CreateFolder
from app.services.stage_module.create_stage import CreateStage
from app.services.stage_module.delete_folder import DeleteFolder
from app.services.stage_module.delete_stage import DeleteStage
from app.services.stage_module.list_folders import ListFolders
from app.services.stage_module.list_stages import ListStages
from app.services.stage_module.list_user_stages import ListUserStages
from app.services.stage_module.set_stage_done import SetStageDone
from app.services.stage_module.update_folder import UpdateFolder
from app.services.stage_module.update_stage import UpdateStage

NOW = datetime.now(tz=UTC)


def _stage(text: str = "Step 1") -> Stage:
    return Stage(id=uuid4(), text=text, created_at=NOW, title=None)


def _folder(title: str = "Folder 1", order: int = 0) -> StageFolder:
    return StageFolder(id=uuid4(), title=title, order=order, created_at=NOW)


def _user_stage(done: bool = False) -> UserStage:
    return UserStage(user_id=uuid4(), stage_id=uuid4(), done=done, updated_at=NOW)


def _repo(**kwargs: object) -> AsyncMock:
    repo = AsyncMock()
    for attr, val in kwargs.items():
        if isinstance(val, Exception):
            getattr(repo, attr).side_effect = val
        else:
            getattr(repo, attr).return_value = val
    return repo


@pytest.mark.asyncio
async def test_create_stage() -> None:
    stage = _stage()
    repo = _repo(create=stage)
    result = await CreateStage(repo).execute(text="Step 1")
    assert result.text == "Step 1"
    repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_update_stage_happy_path() -> None:
    stage = _stage("old")
    updated = Stage(id=stage.id, text="new", created_at=stage.created_at, title=None)
    repo = _repo(get_by_id=stage, update=updated)
    result = await UpdateStage(repo).execute(stage_id=stage.id, text="new")
    assert result.text == "new"


@pytest.mark.asyncio
async def test_update_stage_not_found() -> None:
    repo = _repo(get_by_id=None)
    with pytest.raises(StageNotFound):
        await UpdateStage(repo).execute(stage_id=uuid4(), text="x")


@pytest.mark.asyncio
async def test_delete_stage_happy_path() -> None:
    stage = _stage()
    repo = _repo(get_by_id=stage, delete=None)
    await DeleteStage(repo).execute(stage_id=stage.id)
    repo.delete.assert_called_once_with(stage.id)


@pytest.mark.asyncio
async def test_delete_stage_not_found() -> None:
    repo = _repo(get_by_id=None)
    with pytest.raises(StageNotFound):
        await DeleteStage(repo).execute(stage_id=uuid4())


@pytest.mark.asyncio
async def test_list_stages() -> None:
    stages = [_stage("A"), _stage("B")]
    repo = _repo(list_all=stages)
    result = await ListStages(repo).execute()
    assert len(result) == 2


@pytest.mark.asyncio
async def test_list_user_stages() -> None:
    user_id = uuid4()
    items = [(_user_stage(), _stage()), (_user_stage(done=True), _stage("Step 2"))]
    repo = _repo(list_for_user=items)
    result = await ListUserStages(repo).execute(user_id=user_id)
    assert len(result) == 2


@pytest.mark.asyncio
async def test_attach_stage_happy_path() -> None:
    stage = _stage()
    us = UserStage(user_id=uuid4(), stage_id=stage.id, done=False, updated_at=NOW)
    repo = _repo(get_by_id=stage, attach_to_user=us)
    result = await AttachStage(repo).execute(user_id=us.user_id, stage_id=stage.id)
    assert result.stage_id == stage.id


@pytest.mark.asyncio
async def test_attach_stage_not_found() -> None:
    repo = _repo(get_by_id=None)
    with pytest.raises(StageNotFound):
        await AttachStage(repo).execute(user_id=uuid4(), stage_id=uuid4())


@pytest.mark.asyncio
async def test_attach_stage_already_attached() -> None:
    stage = _stage()
    repo = _repo(get_by_id=stage, attach_to_user=StageAlreadyAttached("dup"))
    with pytest.raises(StageAlreadyAttached):
        await AttachStage(repo).execute(user_id=uuid4(), stage_id=stage.id)


@pytest.mark.asyncio
async def test_set_stage_done() -> None:
    user_id = uuid4()
    stage_id = uuid4()
    us = UserStage(user_id=user_id, stage_id=stage_id, done=True, updated_at=NOW)
    repo = _repo(set_done=us)
    result = await SetStageDone(repo).execute(user_id=user_id, stage_id=stage_id, done=True)
    assert result.done is True


# ── stage folders ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_stage_with_folder() -> None:
    folder_id = uuid4()
    stage = _stage()
    repo = _repo(create=stage)
    await CreateStage(repo).execute(text="Step 1", folder_id=folder_id, order=3)
    created = repo.create.call_args.args[0]
    assert created.folder_id == folder_id
    assert created.order == 3


@pytest.mark.asyncio
async def test_update_stage_moves_folder_and_order() -> None:
    stage = Stage(id=uuid4(), text="s", created_at=NOW, title=None, folder_id=uuid4(), order=1)
    new_folder = uuid4()
    repo = _repo(get_by_id=stage, update=stage)
    await UpdateStage(repo).execute(stage_id=stage.id, folder_id=new_folder, order=5)
    saved = repo.update.call_args.args[0]
    assert saved.folder_id == new_folder
    assert saved.order == 5


@pytest.mark.asyncio
async def test_update_stage_can_clear_folder() -> None:
    stage = Stage(id=uuid4(), text="s", created_at=NOW, title=None, folder_id=uuid4(), order=1)
    repo = _repo(get_by_id=stage, update=stage)
    await UpdateStage(repo).execute(stage_id=stage.id, folder_id=None)
    saved = repo.update.call_args.args[0]
    assert saved.folder_id is None


@pytest.mark.asyncio
async def test_update_stage_keeps_folder_when_omitted() -> None:
    keep = uuid4()
    stage = Stage(id=uuid4(), text="s", created_at=NOW, title=None, folder_id=keep, order=1)
    repo = _repo(get_by_id=stage, update=stage)
    await UpdateStage(repo).execute(stage_id=stage.id, text="new")
    saved = repo.update.call_args.args[0]
    assert saved.folder_id == keep


@pytest.mark.asyncio
async def test_create_folder() -> None:
    folder = _folder()
    repo = _repo(create_folder=folder)
    result = await CreateFolder(repo).execute(title="Folder 1", order=2)
    assert result.title == "Folder 1"
    repo.create_folder.assert_called_once()


@pytest.mark.asyncio
async def test_update_folder_happy_path() -> None:
    folder = _folder("old")
    repo = _repo(get_folder_by_id=folder, update_folder=folder)
    await UpdateFolder(repo).execute(folder_id=folder.id, title="new")
    saved = repo.update_folder.call_args.args[0]
    assert saved.title == "new"


@pytest.mark.asyncio
async def test_update_folder_not_found() -> None:
    repo = _repo(get_folder_by_id=None)
    with pytest.raises(StageFolderNotFound):
        await UpdateFolder(repo).execute(folder_id=uuid4(), title="x")


@pytest.mark.asyncio
async def test_delete_folder_happy_path() -> None:
    folder = _folder()
    repo = _repo(get_folder_by_id=folder, delete_folder=None)
    await DeleteFolder(repo).execute(folder_id=folder.id)
    repo.delete_folder.assert_called_once_with(folder.id)


@pytest.mark.asyncio
async def test_delete_folder_not_found() -> None:
    repo = _repo(get_folder_by_id=None)
    with pytest.raises(StageFolderNotFound):
        await DeleteFolder(repo).execute(folder_id=uuid4())


@pytest.mark.asyncio
async def test_list_folders() -> None:
    repo = _repo(list_folders=[_folder("A"), _folder("B")])
    result = await ListFolders(repo).execute()
    assert len(result) == 2
