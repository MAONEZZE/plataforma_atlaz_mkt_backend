from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.config.dependencies.auth_deps import get_current_user
from app.api.controllers.product_module.product_dto.product_dto import ProductOut
from app.database.product_module.product_repo import SqlAlchemyProductRepository
from app.database.shared.db_factory import get_session
from app.domain.auth_module.auth_model import User as AuthUser
from app.domain.shared.base_exceptions import AppException
from app.domain.product_module.product_exceptions import ProductNotFound
from app.services.product_module.list_products import ListProducts

router = APIRouter(tags=["products"])


def _repo(session: AsyncSession) -> SqlAlchemyProductRepository:
    return SqlAlchemyProductRepository(session)


def _list_products(session: AsyncSession = Depends(get_session)) -> ListProducts:
    return ListProducts(_repo(session))


@router.get("/products", response_model=list[ProductOut])
async def list_products(
    _user: AuthUser = Depends(get_current_user),
    use_case: ListProducts = Depends(_list_products),
) -> list[ProductOut]:
    products = await use_case.execute()
    return [ProductOut(id=p.id, name=p.name, value=p.value, created_at=p.created_at) for p in products]


@router.get("/products/{product_id}", response_model=ProductOut)
async def get_product(
    product_id: UUID,
    _user: AuthUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ProductOut:
    product = await SqlAlchemyProductRepository(session).get_by_id(product_id)
    if product is None:
        raise AppException("PRODUCT_NOT_FOUND", f"Product {product_id} not found.", 404)
    return ProductOut(id=product.id, name=product.name, value=product.value, created_at=product.created_at)
