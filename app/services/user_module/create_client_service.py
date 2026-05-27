from dataclasses import dataclass

import structlog

from app.domain.shared.utils import now_sp
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
    ) -> None:
        self._repo = repo
        self._gateway = gateway

    async def execute(self, inp: CreateClientInput) -> User:
        Password(inp.password)
        if inp.phone is not None:
            Telefone(inp.phone)

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
            description=None,
            photo_url=None,
            role="cliente",
            inactive=False,
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

        if inp.phone is not None:
            try:
                await self._repo.update(user)
            except Exception:
                logger.warning(
                    "phone_update_failed_after_create",
                    auth_user_id=str(user_id),
                )

        return user
