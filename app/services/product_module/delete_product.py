from uuid import UUID

from app.domain.product_module.product_exceptions import ProductNotFound
from app.domain.product_module.product_repo_interface import ProductRepository


class DeleteProduct:
    def __init__(self, repo: ProductRepository) -> None:
        self._repo = repo

    async def execute(self, product_id: UUID) -> None:
        product = await self._repo.get_by_id(product_id)
        if product is None:
            raise ProductNotFound(f"Product {product_id} not found.")
        await self._repo.delete(product_id)
