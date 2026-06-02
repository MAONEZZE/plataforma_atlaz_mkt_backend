from dataclasses import dataclass
from uuid import UUID

import structlog

from app.domain.product_module.product_exceptions import ProductNotFound
from app.domain.product_module.product_repo_interface import ProductRepository
from app.domain.stage_module.stage_repo_interface import StageRepository
from app.domain.user_module.user_exceptions import UserNotFound
from app.domain.user_module.user_model import User
from app.domain.user_module.user_repo_interface import UserRepository

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class UpdateClientInput:
    client_id: UUID
    name: str | None = None
    phone: str | None = None
    description: str | None = None
    product_id: UUID | None = None
    set_product: bool = False
    stage_ids: tuple[UUID, ...] | None = None


class UpdateClient:
    def __init__(
        self,
        repo: UserRepository,
        product_repo: ProductRepository | None = None,
        stage_repo: StageRepository | None = None,
    ) -> None:
        self._repo = repo
        self._product_repo = product_repo
        self._stage_repo = stage_repo

    async def execute(self, inp: UpdateClientInput) -> User:
        user = await self._repo.get_by_id(inp.client_id)
        if user is None:
            raise UserNotFound(f"Client {inp.client_id} not found.")

        if inp.name is not None:
            user.name = inp.name
        if inp.phone is not None:
            user.phone = inp.phone
        if inp.description is not None:
            user.description = inp.description

        await self._repo.update(user)

        if inp.set_product:
            product_name: str | None = None
            if inp.product_id is not None and self._product_repo is not None:
                product = await self._product_repo.get_by_id(inp.product_id)
                if product is None:
                    raise ProductNotFound(f"Product {inp.product_id} not found.")
                product_name = product.name
            await self._repo.assign_product(inp.client_id, inp.product_id)
            user.product_id = inp.product_id
            user.product_name = product_name

        if inp.stage_ids is not None and self._stage_repo is not None:
            await self._sync_stages(inp.client_id, set(inp.stage_ids))

        return user

    async def _sync_stages(self, client_id: UUID, desired: set[UUID]) -> None:
        current_rows = await self._stage_repo.list_for_user(client_id)  # type: ignore[union-attr]
        current_ids = {us.stage_id for us, _ in current_rows}

        for stage_id in current_ids - desired:
            await self._stage_repo.detach_from_user(client_id, stage_id)  # type: ignore[union-attr]

        for stage_id in desired - current_ids:
            try:
                await self._stage_repo.attach_to_user(client_id, stage_id)  # type: ignore[union-attr]
            except Exception:
                logger.warning("stage_attach_failed_on_update", stage_id=str(stage_id))
