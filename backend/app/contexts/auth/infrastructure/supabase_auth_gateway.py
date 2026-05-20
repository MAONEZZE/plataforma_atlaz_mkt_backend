from supabase import Client
from supabase_auth.errors import AuthApiError

from app.contexts.auth.application.dtos import TokensDTO
from app.contexts.auth.domain.exceptions import InvalidCredentials, LogoutFailed


class SupabaseAuthGatewayImpl:
    def __init__(self, anon_client: Client, admin_client: Client) -> None:
        self._anon = anon_client
        self._admin = admin_client

    def sign_in_with_password(self, email: str, password: str) -> TokensDTO:
        try:
            resp = self._anon.auth.sign_in_with_password({"email": email, "password": password})
        except AuthApiError as exc:
            raise InvalidCredentials("Email ou senha inválidos.") from exc
        session = resp.session
        if not session:
            raise InvalidCredentials("Email ou senha inválidos.")
        return TokensDTO(
            access_token=session.access_token,
            refresh_token=session.refresh_token,
            expires_in=session.expires_in,
            token_type=session.token_type,
        )

    def sign_out(self, access_token: str) -> None:
        try:
            self._admin.auth.admin.sign_out(access_token)
        except AuthApiError as exc:
            raise LogoutFailed(str(exc)) from exc
