from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.config.dependencies.auth_deps import get_current_user, require_admin
from app.api.controllers.product_module.product_routes.admin_router import (
    _assign_product,
    _create_product,
    _delete_product,
    _update_product,
)
from app.api.controllers.product_module.product_routes.product_router import (
    _list_products,
)
from app.domain.auth_module.auth_model import User
from app.domain.product_module.product_exceptions import ProductInUse, ProductNotFound
from app.domain.product_module.product_model import Product
from app.main import app

NOW = datetime.now(tz=timezone.utc)


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


def _product() -> Product:
    return Product(id=uuid4(), name="Pro Plan", value=Decimal("99.90"), description=None, created_at=NOW)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


# ── POST /admin/products ───────────────────────────────────────────────────────

def test_create_product_201(client: TestClient) -> None:
    admin = _admin()
    product = _product()
    uc = _uc(execute_return=product)
    app.dependency_overrides[require_admin] = lambda: admin
    app.dependency_overrides[_create_product] = lambda: uc
    try:
        r = client.post("/api/v1/admin/products", json={"name": "Pro Plan", "value": "99.90"})
        assert r.status_code == 201
        assert r.json()["name"] == "Pro Plan"
    finally:
        app.dependency_overrides.clear()


def test_create_product_403_for_cliente(client: TestClient) -> None:
    user = _cliente()
    app.dependency_overrides[get_current_user] = lambda: user
    try:
        r = client.post("/api/v1/admin/products", json={"name": "x", "value": "1.00"})
        assert r.status_code == 403
    finally:
        app.dependency_overrides.clear()


# ── PATCH /admin/products/{id} ─────────────────────────────────────────────────

def test_update_product_200(client: TestClient) -> None:
    admin = _admin()
    product = _product()
    uc = _uc(execute_return=product)
    app.dependency_overrides[require_admin] = lambda: admin
    app.dependency_overrides[_update_product] = lambda: uc
    try:
        r = client.patch(f"/api/v1/admin/products/{uuid4()}", json={"name": "Updated"})
        assert r.status_code == 200
    finally:
        app.dependency_overrides.clear()


def test_update_product_404(client: TestClient) -> None:
    admin = _admin()
    uc = _uc(execute_raises=ProductNotFound("nope"))
    app.dependency_overrides[require_admin] = lambda: admin
    app.dependency_overrides[_update_product] = lambda: uc
    try:
        r = client.patch(f"/api/v1/admin/products/{uuid4()}", json={"name": "x"})
        assert r.status_code == 404
    finally:
        app.dependency_overrides.clear()


# ── DELETE /admin/products/{id} ────────────────────────────────────────────────

def test_delete_product_204(client: TestClient) -> None:
    admin = _admin()
    uc = _uc(execute_return=None)
    app.dependency_overrides[require_admin] = lambda: admin
    app.dependency_overrides[_delete_product] = lambda: uc
    try:
        r = client.delete(f"/api/v1/admin/products/{uuid4()}")
        assert r.status_code == 204
    finally:
        app.dependency_overrides.clear()


def test_delete_product_409_in_use(client: TestClient) -> None:
    admin = _admin()
    uc = _uc(execute_raises=ProductInUse("in use"))
    app.dependency_overrides[require_admin] = lambda: admin
    app.dependency_overrides[_delete_product] = lambda: uc
    try:
        r = client.delete(f"/api/v1/admin/products/{uuid4()}")
        assert r.status_code == 409
    finally:
        app.dependency_overrides.clear()


# ── PATCH /admin/clients/{uid}/product ────────────────────────────────────────

def test_assign_product_200(client: TestClient) -> None:
    admin = _admin()
    uc = _uc(execute_return=None)
    app.dependency_overrides[require_admin] = lambda: admin
    app.dependency_overrides[_assign_product] = lambda: uc
    try:
        r = client.patch(f"/api/v1/admin/clients/{uuid4()}/product", json={"product_id": str(uuid4())})
        assert r.status_code == 204
    finally:
        app.dependency_overrides.clear()


# ── GET /products ──────────────────────────────────────────────────────────────

def test_list_products_200(client: TestClient) -> None:
    user = _cliente()
    uc = _uc(execute_return=[_product()])
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[_list_products] = lambda: uc
    try:
        r = client.get("/api/v1/products")
        assert r.status_code == 200
        assert len(r.json()) == 1
    finally:
        app.dependency_overrides.clear()


def test_list_products_requires_auth(client: TestClient) -> None:
    r = client.get("/api/v1/products")
    assert r.status_code == 401
