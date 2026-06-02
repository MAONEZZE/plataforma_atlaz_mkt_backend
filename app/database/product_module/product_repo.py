from datetime import datetime
from decimal import Decimal
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.database.shared.sqlalchemy_base import Base
from app.domain.product_module.product_exceptions import ProductInUse, ProductNotFound
from app.domain.product_module.product_model import Product


class ProductModel(Base):
    __tablename__ = "products"
    __table_args__ = {"schema": "ATZ_HUB", "extend_existing": True}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(sa.Text, nullable=False)
    value: Mapped[Decimal] = mapped_column(sa.Numeric(12, 2), nullable=False)
    description: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    cover_photo: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)


def _from_model(m: ProductModel) -> Product:
    return Product(id=m.id, name=m.name, value=m.value, description=m.description, cover_photo=m.cover_photo, created_at=m.created_at)


class SqlAlchemyProductRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, product: Product) -> Product:
        model = ProductModel(
            id=product.id,
            name=product.name,
            value=product.value,
            description=product.description,
            cover_photo=product.cover_photo,
            created_at=product.created_at,
        )
        self._session.add(model)
        await self._session.flush()
        return product

    async def update(self, product: Product) -> Product:
        await self._session.execute(
            sa.update(ProductModel)
            .where(ProductModel.id == product.id)
            .values(name=product.name, value=product.value, description=product.description, cover_photo=product.cover_photo)
        )
        return product

    async def delete(self, product_id: UUID) -> None:
        from app.database.user_module.user_repo import UserModel

        users = await self._session.execute(
            sa.select(sa.func.count()).select_from(UserModel).where(
                UserModel.product_id == product_id
            )
        )
        if users.scalar_one() > 0:
            raise ProductInUse(f"Product {product_id} is still referenced by users.")
        await self._session.execute(
            sa.delete(ProductModel).where(ProductModel.id == product_id)
        )

    async def get_by_id(self, product_id: UUID) -> Product | None:
        result = await self._session.execute(
            sa.select(ProductModel).where(ProductModel.id == product_id)
        )
        m = result.scalar_one_or_none()
        return _from_model(m) if m else None

    async def list_all(self) -> list[Product]:
        result = await self._session.execute(
            sa.select(ProductModel).order_by(ProductModel.created_at)
        )
        return [_from_model(m) for m in result.scalars()]
