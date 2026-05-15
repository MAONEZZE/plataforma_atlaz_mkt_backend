from app.contexts.auth.application.dtos import LoginInput, TokensDTO
from app.contexts.auth.domain.repositories import SupabaseAuthGateway


class Login:
    def __init__(self, gateway: SupabaseAuthGateway) -> None:
        self._gateway = gateway

    async def execute(self, inp: LoginInput) -> TokensDTO:
        return self._gateway.sign_in_with_password(inp.email, inp.password)
