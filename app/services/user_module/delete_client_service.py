from dataclasses import dataclass
from uuid import UUID

import structlog

from app.domain.user_module.user_exceptions import UserNotFound
from app.domain.user_module.user_repo_interface import UserRepository
from app.services.user_module.supabase_admin_gateway import SupabaseAdminUserGateway

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class DeleteClientInput:
    client_id: UUID


class DeleteClient:
    def __init__(self, repo: UserRepository, gateway: SupabaseAdminUserGateway) -> None:
        self._repo = repo
        self._gateway = gateway

    async def execute(self, inp: DeleteClientInput) -> None:
        user = await self._repo.get_by_id(inp.client_id)
        if user is None:
            raise UserNotFound(f"Client {inp.client_id} not found.")

        self._gateway.delete_user(inp.client_id)
        await self._repo.deactivate(inp.client_id)
        logger.info("client_deleted", client_id=str(inp.client_id))
