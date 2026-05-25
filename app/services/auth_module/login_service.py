from app.api.controllers.auth_module.auth_dto.auth_dto import LoginInput, TokensDTO
from app.domain.auth_module.auth_repo_interface import SupabaseAuthGateway


class Login:
    def __init__(self, gateway: SupabaseAuthGateway) -> None:
        self._gateway = gateway

    async def execute(self, inp: LoginInput) -> TokensDTO:
        return self._gateway.sign_in_with_password(inp.email, inp.password)
