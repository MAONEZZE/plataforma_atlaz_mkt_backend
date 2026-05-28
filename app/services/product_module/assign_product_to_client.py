from uuid import UUID

from app.domain.product_module.product_exceptions import ProductNotFound
from app.domain.product_module.product_repo_interface import ProductRepository
from app.domain.user_module.user_repo_interface import UserRepository


class AssignProductToClient:
    def __init__(self, product_repo: ProductRepository, user_repo: UserRepository) -> None:
        self._product_repo = product_repo
        self._user_repo = user_repo

    async def execute(self, user_id: UUID, product_id: UUID | None) -> None:
        if product_id is not None:
            product = await self._product_repo.get_by_id(product_id)
            if product is None:
                raise ProductNotFound(f"Product {product_id} not found.")
        await self._user_repo.assign_product(user_id, product_id)
