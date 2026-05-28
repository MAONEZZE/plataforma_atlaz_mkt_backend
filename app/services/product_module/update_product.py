from dataclasses import replace
from decimal import Decimal
from uuid import UUID

from app.domain.product_module.product_exceptions import ProductNotFound
from app.domain.product_module.product_model import Product
from app.domain.product_module.product_repo_interface import ProductRepository


class UpdateProduct:
    def __init__(self, repo: ProductRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        product_id: UUID,
        name: str | None = None,
        value: Decimal | None = None,
    ) -> Product:
        product = await self._repo.get_by_id(product_id)
        if product is None:
            raise ProductNotFound(f"Product {product_id} not found.")
        updated = replace(
            product,
            name=name if name is not None else product.name,
            value=value if value is not None else product.value,
        )
        return await self._repo.update(updated)
