from app.domain.product_module.product_model import Product
from app.domain.product_module.product_repo_interface import ProductRepository


class ListProducts:
    def __init__(self, repo: ProductRepository) -> None:
        self._repo = repo

    async def execute(self) -> list[Product]:
        return await self._repo.list_all()
