from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.domain.product_module.product_exceptions import ProductInUse, ProductNotFound
from app.domain.product_module.product_model import Product
from app.services.product_module.assign_product_to_client import AssignProductToClient
from app.services.product_module.create_product import CreateProduct
from app.services.product_module.delete_product import DeleteProduct
from app.services.product_module.list_products import ListProducts
from app.services.product_module.update_product import UpdateProduct

NOW = datetime.now(tz=timezone.utc)


def _product(name: str = "Pro Plan", value: Decimal = Decimal("99.90")) -> Product:
    return Product(id=uuid4(), name=name, value=value, created_at=NOW)


def _repo(**kwargs: object) -> AsyncMock:
    repo = AsyncMock()
    for attr, val in kwargs.items():
        if isinstance(val, Exception):
            getattr(repo, attr).side_effect = val
        else:
            getattr(repo, attr).return_value = val
    return repo


@pytest.mark.asyncio
async def test_create_product() -> None:
    product = _product()
    repo = _repo(create=product)
    result = await CreateProduct(repo).execute(name="Pro Plan", value=Decimal("99.90"))
    assert result.name == "Pro Plan"
    repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_update_product_happy_path() -> None:
    product = _product()
    updated = Product(id=product.id, name="New Name", value=Decimal("149.00"), created_at=NOW)
    repo = _repo(get_by_id=product, update=updated)
    result = await UpdateProduct(repo).execute(product_id=product.id, name="New Name", value=Decimal("149.00"))
    assert result.name == "New Name"


@pytest.mark.asyncio
async def test_update_product_not_found() -> None:
    repo = _repo(get_by_id=None)
    with pytest.raises(ProductNotFound):
        await UpdateProduct(repo).execute(product_id=uuid4(), name="x")


@pytest.mark.asyncio
async def test_delete_product_happy_path() -> None:
    product = _product()
    repo = _repo(get_by_id=product, delete=None)
    await DeleteProduct(repo).execute(product_id=product.id)
    repo.delete.assert_called_once_with(product.id)


@pytest.mark.asyncio
async def test_delete_product_not_found() -> None:
    repo = _repo(get_by_id=None)
    with pytest.raises(ProductNotFound):
        await DeleteProduct(repo).execute(product_id=uuid4())


@pytest.mark.asyncio
async def test_delete_product_in_use() -> None:
    product = _product()
    repo = _repo(get_by_id=product, delete=ProductInUse("in use"))
    with pytest.raises(ProductInUse):
        await DeleteProduct(repo).execute(product_id=product.id)


@pytest.mark.asyncio
async def test_list_products() -> None:
    products = [_product("A"), _product("B")]
    repo = _repo(list_all=products)
    result = await ListProducts(repo).execute()
    assert len(result) == 2


@pytest.mark.asyncio
async def test_assign_product_to_client_happy_path() -> None:
    product = _product()
    product_repo = _repo(get_by_id=product)
    user_repo = AsyncMock()
    user_repo.assign_product.return_value = None
    await AssignProductToClient(product_repo, user_repo).execute(
        user_id=uuid4(), product_id=product.id
    )
    user_repo.assign_product.assert_called_once()


@pytest.mark.asyncio
async def test_assign_product_not_found() -> None:
    product_repo = _repo(get_by_id=None)
    user_repo = AsyncMock()
    with pytest.raises(ProductNotFound):
        await AssignProductToClient(product_repo, user_repo).execute(
            user_id=uuid4(), product_id=uuid4()
        )


@pytest.mark.asyncio
async def test_assign_product_none_clears() -> None:
    product_repo = AsyncMock()
    user_repo = AsyncMock()
    user_repo.assign_product.return_value = None
    await AssignProductToClient(product_repo, user_repo).execute(
        user_id=uuid4(), product_id=None
    )
    product_repo.get_by_id.assert_not_called()
    user_repo.assign_product.assert_called_once()
