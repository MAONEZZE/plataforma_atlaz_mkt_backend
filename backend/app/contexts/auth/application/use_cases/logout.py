from app.contexts.auth.domain.repositories import SupabaseAuthGateway


class Logout:
    def __init__(self, gateway: SupabaseAuthGateway) -> None:
        self._gateway = gateway

    async def execute(self, access_token: str) -> None:
        self._gateway.sign_out(access_token)
