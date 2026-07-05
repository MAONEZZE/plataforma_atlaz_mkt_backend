from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.config.dependencies.auth_deps import get_current_user, require_admin
from app.api.controllers.stage_module.stage_routes.admin_router import (
    _attach_stage,
    _create_folder,
    _create_stage,
    _delete_folder,
    _delete_stage,
    _detach_stage,
    _list_folders,
    _list_stages,
    _update_folder,
    _update_stage,
)
from app.api.controllers.stage_module.stage_routes.stage_router import (
    _list_folders as _list_folders_for_user,
    _list_user_stages,
    _set_stage_done,
)
from app.domain.auth_module.auth_model import User
from app.domain.stage_module.stage_exceptions import (
    StageAlreadyAttached,
    StageFolderNotFound,
    StageNotFound,
)
from app.domain.stage_module.stage_model import Stage, StageFolder, UserStage
from app.main import app

NOW = datetime.now(tz=UTC)


def _admin() -> User:
    return User(id=uuid4(), email="a@test.com", role="admin", inactive=False)


def _cliente() -> User:
    return User(id=uuid4(), email="c@test.com", role="cliente", inactive=False)


def _uc(**kwargs: object) -> AsyncMock:
    m = AsyncMock()
    if "execute_return" in kwargs:
        m.execute.return_value = kwargs["execute_return"]
    elif "execute_raises" in kwargs:
        m.execute.side_effect = kwargs["execute_raises"]
    return m


def _stage() -> Stage:
    return Stage(id=uuid4(), text="Step 1", created_at=NOW, title=None)


def _user_stage(user_id: object = None) -> UserStage:
    return UserStage(user_id=user_id or uuid4(), stage_id=uuid4(), done=False, updated_at=NOW)


def _folder(folder_id: object = None, title: str = "Folder 1", order: int = 0) -> StageFolder:
    return StageFolder(id=folder_id or uuid4(), title=title, order=order, created_at=NOW)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


# ── POST /admin/stages ─────────────────────────────────────────────────────────

def test_create_stage_201(client: TestClient) -> None:
    admin = _admin()
    stage = _stage()
    uc = _uc(execute_return=stage)
    app.dependency_overrides[require_admin] = lambda: admin
    app.dependency_overrides[_create_stage] = lambda: uc
    try:
        r = client.post("/api/v1/admin/stages", json={"text": "Step 1"})
        assert r.status_code == 201
        assert r.json()["text"] == "Step 1"
    finally:
        app.dependency_overrides.clear()


def test_create_stage_403_for_cliente(client: TestClient) -> None:
    user = _cliente()
    app.dependency_overrides[get_current_user] = lambda: user
    try:
        r = client.post("/api/v1/admin/stages", json={"text": "Step 1"})
        assert r.status_code == 403
    finally:
        app.dependency_overrides.clear()


# ── GET /admin/stages ──────────────────────────────────────────────────────────

def test_list_stages_200(client: TestClient) -> None:
    admin = _admin()
    uc = _uc(execute_return=[_stage(), _stage()])
    app.dependency_overrides[require_admin] = lambda: admin
    app.dependency_overrides[_list_stages] = lambda: uc
    try:
        r = client.get("/api/v1/admin/stages")
        assert r.status_code == 200
        assert len(r.json()) == 2
    finally:
        app.dependency_overrides.clear()


# ── PATCH /admin/stages/{id} ───────────────────────────────────────────────────

def test_update_stage_200(client: TestClient) -> None:
    admin = _admin()
    stage = _stage()
    uc = _uc(execute_return=stage)
    app.dependency_overrides[require_admin] = lambda: admin
    app.dependency_overrides[_update_stage] = lambda: uc
    try:
        r = client.patch(f"/api/v1/admin/stages/{uuid4()}", json={"text": "Updated"})
        assert r.status_code == 200
    finally:
        app.dependency_overrides.clear()


def test_update_stage_404(client: TestClient) -> None:
    admin = _admin()
    uc = _uc(execute_raises=StageNotFound("nope"))
    app.dependency_overrides[require_admin] = lambda: admin
    app.dependency_overrides[_update_stage] = lambda: uc
    try:
        r = client.patch(f"/api/v1/admin/stages/{uuid4()}", json={"text": "x"})
        assert r.status_code == 404
    finally:
        app.dependency_overrides.clear()


# ── DELETE /admin/stages/{id} ──────────────────────────────────────────────────

def test_delete_stage_204(client: TestClient) -> None:
    admin = _admin()
    uc = _uc(execute_return=None)
    app.dependency_overrides[require_admin] = lambda: admin
    app.dependency_overrides[_delete_stage] = lambda: uc
    try:
        r = client.delete(f"/api/v1/admin/stages/{uuid4()}")
        assert r.status_code == 204
    finally:
        app.dependency_overrides.clear()


# ── POST /admin/clients/{uid}/stages/{sid} ────────────────────────────────────

def test_attach_stage_201(client: TestClient) -> None:
    admin = _admin()
    us = _user_stage()
    uc = _uc(execute_return=us)
    app.dependency_overrides[require_admin] = lambda: admin
    app.dependency_overrides[_attach_stage] = lambda: uc
    try:
        r = client.post(f"/api/v1/admin/clients/{uuid4()}/stages/{uuid4()}")
        assert r.status_code == 201
    finally:
        app.dependency_overrides.clear()


def test_attach_stage_409_duplicate(client: TestClient) -> None:
    admin = _admin()
    uc = _uc(execute_raises=StageAlreadyAttached("dup"))
    app.dependency_overrides[require_admin] = lambda: admin
    app.dependency_overrides[_attach_stage] = lambda: uc
    try:
        r = client.post(f"/api/v1/admin/clients/{uuid4()}/stages/{uuid4()}")
        assert r.status_code == 409
    finally:
        app.dependency_overrides.clear()


# ── DELETE /admin/clients/{uid}/stages/{sid} ──────────────────────────────────

def test_detach_stage_204(client: TestClient) -> None:
    admin = _admin()
    uc = _uc(execute_return=None)
    app.dependency_overrides[require_admin] = lambda: admin
    app.dependency_overrides[_detach_stage] = lambda: uc
    try:
        r = client.delete(f"/api/v1/admin/clients/{uuid4()}/stages/{uuid4()}")
        assert r.status_code == 204
    finally:
        app.dependency_overrides.clear()


# ── stage folders ──────────────────────────────────────────────────────────────

def test_create_folder_201(client: TestClient) -> None:
    admin = _admin()
    uc = _uc(execute_return=_folder())
    app.dependency_overrides[require_admin] = lambda: admin
    app.dependency_overrides[_create_folder] = lambda: uc
    try:
        r = client.post("/api/v1/admin/stage-folders", json={"title": "Folder 1"})
        assert r.status_code == 201
        assert r.json()["title"] == "Folder 1"
    finally:
        app.dependency_overrides.clear()


def test_list_folders_200(client: TestClient) -> None:
    admin = _admin()
    uc = _uc(execute_return=[_folder(), _folder()])
    app.dependency_overrides[require_admin] = lambda: admin
    app.dependency_overrides[_list_folders] = lambda: uc
    try:
        r = client.get("/api/v1/admin/stage-folders")
        assert r.status_code == 200
        assert len(r.json()) == 2
    finally:
        app.dependency_overrides.clear()


def test_update_folder_404(client: TestClient) -> None:
    admin = _admin()
    uc = _uc(execute_raises=StageFolderNotFound("nope"))
    app.dependency_overrides[require_admin] = lambda: admin
    app.dependency_overrides[_update_folder] = lambda: uc
    try:
        r = client.patch(f"/api/v1/admin/stage-folders/{uuid4()}", json={"title": "x"})
        assert r.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_delete_folder_204(client: TestClient) -> None:
    admin = _admin()
    uc = _uc(execute_return=None)
    app.dependency_overrides[require_admin] = lambda: admin
    app.dependency_overrides[_delete_folder] = lambda: uc
    try:
        r = client.delete(f"/api/v1/admin/stage-folders/{uuid4()}")
        assert r.status_code == 204
    finally:
        app.dependency_overrides.clear()


# ── GET /stages/me ─────────────────────────────────────────────────────────────

def test_list_my_stages_200(client: TestClient) -> None:
    user = _cliente()
    uc = _uc(execute_return=[(_user_stage(user.id), _stage())])
    folders_uc = _uc(execute_return=[])
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[_list_user_stages] = lambda: uc
    app.dependency_overrides[_list_folders_for_user] = lambda: folders_uc
    try:
        r = client.get("/api/v1/stages/me")
        assert r.status_code == 200
        assert len(r.json()) == 1
    finally:
        app.dependency_overrides.clear()


def test_list_my_stages_includes_folder_title_and_order(client: TestClient) -> None:
    user = _cliente()
    folder = _folder(title="Sprint 1")
    stage = Stage(id=uuid4(), text="Step 1", created_at=NOW, title=None, folder_id=folder.id, order=2)
    uc = _uc(execute_return=[(_user_stage(user.id), stage)])
    folders_uc = _uc(execute_return=[folder])
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[_list_user_stages] = lambda: uc
    app.dependency_overrides[_list_folders_for_user] = lambda: folders_uc
    try:
        r = client.get("/api/v1/stages/me")
        assert r.status_code == 200
        item = r.json()[0]
        assert item["folder_title"] == "Sprint 1"
        assert item["order"] == 2
    finally:
        app.dependency_overrides.clear()


def test_list_my_stages_folder_title_null_without_folder(client: TestClient) -> None:
    user = _cliente()
    stage = _stage()
    uc = _uc(execute_return=[(_user_stage(user.id), stage)])
    folders_uc = _uc(execute_return=[])
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[_list_user_stages] = lambda: uc
    app.dependency_overrides[_list_folders_for_user] = lambda: folders_uc
    try:
        r = client.get("/api/v1/stages/me")
        assert r.status_code == 200
        item = r.json()[0]
        assert item["folder_title"] is None
    finally:
        app.dependency_overrides.clear()


# ── PATCH /stages/me/{stage_id} ───────────────────────────────────────────────

def test_set_done_200(client: TestClient) -> None:
    user = _cliente()
    us = UserStage(user_id=user.id, stage_id=uuid4(), done=True, updated_at=NOW)
    uc = _uc(execute_return=us)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[_set_stage_done] = lambda: uc
    try:
        r = client.patch(f"/api/v1/stages/me/{uuid4()}", json={"done": True})
        assert r.status_code == 200
        assert r.json()["done"] is True
    finally:
        app.dependency_overrides.clear()


def test_set_done_404(client: TestClient) -> None:
    user = _cliente()
    uc = _uc(execute_raises=StageNotFound("nope"))
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[_set_stage_done] = lambda: uc
    try:
        r = client.patch(f"/api/v1/stages/me/{uuid4()}", json={"done": True})
        assert r.status_code == 404
    finally:
        app.dependency_overrides.clear()
