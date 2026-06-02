from decimal import Decimal
from uuid import uuid4

from app.domain.product_module.product_model import Product
from app.domain.product_module.product_repo_interface import ProductRepository
from app.domain.shared.utils import now_sp


class CreateProduct:
    def __init__(self, repo: ProductRepository) -> None:
        self._repo = repo

    async def execute(self, name: str, value: Decimal, description: str | None = None, cover_photo: str | None = None) -> Product:
        product = Product(id=uuid4(), name=name, value=value, description=description, cover_photo=cover_photo, created_at=now_sp())
        return await self._repo.create(product)
