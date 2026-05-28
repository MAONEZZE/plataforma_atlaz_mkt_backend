from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.domain.stage_module.stage_exceptions import StageAlreadyAttached, StageNotFound
from app.domain.stage_module.stage_model import Stage, UserStage
from app.services.stage_module.attach_stage import AttachStage
from app.services.stage_module.create_stage import CreateStage
from app.services.stage_module.delete_stage import DeleteStage
from app.services.stage_module.list_stages import ListStages
from app.services.stage_module.list_user_stages import ListUserStages
from app.services.stage_module.set_stage_done import SetStageDone
from app.services.stage_module.update_stage import UpdateStage

NOW = datetime.now(tz=timezone.utc)


def _stage(text: str = "Step 1") -> Stage:
    return Stage(id=uuid4(), text=text, created_at=NOW)


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
    updated = Stage(id=stage.id, text="new", created_at=stage.created_at)
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
    items = [_user_stage(), _user_stage(done=True)]
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
