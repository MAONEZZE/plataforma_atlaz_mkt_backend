from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.config.dependencies.auth_deps import require_admin
from app.api.controllers.product_module.product_dto.product_dto import (
    AssignProductBody,
    ProductIn,
    ProductOut,
    ProductPatchIn,
)
from app.database.product_module.product_repo import SqlAlchemyProductRepository
from app.database.shared.db_factory import get_session
from app.database.user_module.user_repo import SqlAlchemyUserRepository
from app.domain.auth_module.auth_model import User as AuthUser
from app.domain.product_module.product_exceptions import ProductInUse, ProductNotFound
from app.domain.shared.base_exceptions import AppException
from app.services.product_module.assign_product_to_client import AssignProductToClient
from app.services.product_module.create_product import CreateProduct
from app.services.product_module.delete_product import DeleteProduct
from app.services.product_module.update_product import UpdateProduct

admin_router = APIRouter(prefix="/admin", tags=["admin-products"])


def _product_repo(session: AsyncSession) -> SqlAlchemyProductRepository:
    return SqlAlchemyProductRepository(session)


def _create_product(session: AsyncSession = Depends(get_session)) -> CreateProduct:
    return CreateProduct(_product_repo(session))


def _update_product(session: AsyncSession = Depends(get_session)) -> UpdateProduct:
    return UpdateProduct(_product_repo(session))


def _delete_product(session: AsyncSession = Depends(get_session)) -> DeleteProduct:
    return DeleteProduct(_product_repo(session))


def _assign_product(session: AsyncSession = Depends(get_session)) -> AssignProductToClient:
    return AssignProductToClient(
        product_repo=_product_repo(session),
        user_repo=SqlAlchemyUserRepository(session),
    )


@admin_router.post("/products", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
async def create_product(
    body: ProductIn,
    _admin: AuthUser = Depends(require_admin),
    use_case: CreateProduct = Depends(_create_product),
) -> ProductOut:
    product = await use_case.execute(name=body.name, value=body.value)
    return ProductOut(id=product.id, name=product.name, value=product.value, created_at=product.created_at)


@admin_router.patch("/products/{product_id}", response_model=ProductOut)
async def update_product(
    product_id: UUID,
    body: ProductPatchIn,
    _admin: AuthUser = Depends(require_admin),
    use_case: UpdateProduct = Depends(_update_product),
) -> ProductOut:
    try:
        product = await use_case.execute(product_id=product_id, name=body.name, value=body.value)
    except ProductNotFound as exc:
        raise AppException("PRODUCT_NOT_FOUND", str(exc), 404) from exc
    return ProductOut(id=product.id, name=product.name, value=product.value, created_at=product.created_at)


@admin_router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: UUID,
    _admin: AuthUser = Depends(require_admin),
    use_case: DeleteProduct = Depends(_delete_product),
) -> None:
    try:
        await use_case.execute(product_id=product_id)
    except ProductNotFound as exc:
        raise AppException("PRODUCT_NOT_FOUND", str(exc), 404) from exc
    except ProductInUse as exc:
        raise AppException("PRODUCT_IN_USE", str(exc), 409) from exc


@admin_router.patch("/clients/{user_id}/product", status_code=status.HTTP_204_NO_CONTENT)
async def assign_product_to_client(
    user_id: UUID,
    body: AssignProductBody,
    _admin: AuthUser = Depends(require_admin),
    use_case: AssignProductToClient = Depends(_assign_product),
) -> None:
    try:
        await use_case.execute(user_id=user_id, product_id=body.product_id)
    except ProductNotFound as exc:
        raise AppException("PRODUCT_NOT_FOUND", str(exc), 404) from exc
