import asyncio

from app.domain.auth_module.auth_repo_interface import SupabaseAuthGateway


class Logout:
    def __init__(self, gateway: SupabaseAuthGateway) -> None:
        self._gateway = gateway

    async def execute(self, access_token: str) -> None:
        await asyncio.to_thread(self._gateway.sign_out, access_token)
