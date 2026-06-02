from dataclasses import dataclass
from uuid import UUID

import structlog

from app.domain.product_module.product_exceptions import ProductNotFound
from app.domain.product_module.product_repo_interface import ProductRepository
from app.domain.shared.utils import now_sp
from app.domain.stage_module.stage_exceptions import StageAlreadyAttached, StageNotFound
from app.domain.stage_module.stage_repo_interface import StageRepository
from app.domain.user_module.user_exceptions import UserTriggerSyncFailed
from app.domain.user_module.user_model import User
from app.domain.user_module.user_repo_interface import UserRepository
from app.domain.user_module.user_validator import Password, Telefone
from app.services.user_module.supabase_admin_gateway import SupabaseAdminUserGateway

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class CreateClientInput:
    name: str
    email: str
    password: str
    phone: str | None = None
    description: str | None = None
    product_id: UUID | None = None
    stage_ids: tuple[UUID, ...] = ()


class CreateClient:
    """Cria cliente no Supabase Auth. Trigger DB sincroniza ATZ_HUB.users
    atomicamente com o INSERT em auth.users (mesma transação), portanto o
    retorno bem-sucedido do gateway garante existência da linha. O serviço
    não relê do DB para evitar problemas de visibilidade de snapshot com
    a sessão da requisição."""

    def __init__(
        self,
        repo: UserRepository,
        gateway: SupabaseAdminUserGateway,
        product_repo: ProductRepository | None = None,
        stage_repo: StageRepository | None = None,
    ) -> None:
        self._repo = repo
        self._gateway = gateway
        self._product_repo = product_repo
        self._stage_repo = stage_repo

    async def execute(self, inp: CreateClientInput) -> User:
        Password(inp.password)
        if inp.phone is not None:
            Telefone(inp.phone)

        product_name: str | None = None
        if inp.product_id is not None and self._product_repo is not None:
            product = await self._product_repo.get_by_id(inp.product_id)
            if product is None:
                raise ProductNotFound(f"Product {inp.product_id} not found.")
            product_name = product.name

        user_id = self._gateway.create_user(
            email=inp.email,
            password=inp.password,
            name=inp.name,
            role="cliente",
        )

        now = now_sp()
        user = User(
            id=user_id,
            name=inp.name,
            email=inp.email,
            phone=inp.phone,
            linkedin_url=None,
            instagram_username=None,
            description=inp.description,
            photo_url=None,
            role="cliente",
            inactive=False,
            product_id=inp.product_id,
            product_name=product_name,
            created_at=now,
            updated_at=now,
        )

        try:
            await self._repo.upsert_new(user)
        except Exception:
            logger.error("client_db_insert_failed", auth_user_id=str(user_id))
            raise UserTriggerSyncFailed(
                "Cliente criado em auth.users mas falha ao gravar em ATZ_HUB.users."
            ) from None

        if inp.product_id is not None:
            try:
                await self._repo.assign_product(user_id, inp.product_id)
            except Exception:
                logger.warning("product_assign_failed_after_create", auth_user_id=str(user_id))

        if inp.phone is not None or inp.description is not None:
            try:
                await self._repo.update(user)
            except Exception:
                logger.warning(
                    "profile_update_failed_after_create",
                    auth_user_id=str(user_id),
                )

        if inp.stage_ids and self._stage_repo is not None:
            for stage_id in inp.stage_ids:
                try:
                    await self._stage_repo.attach_to_user(user_id, stage_id)
                except StageAlreadyAttached:
                    pass
                except StageNotFound:
                    logger.warning("stage_not_found_during_create", stage_id=str(stage_id))

        return user
