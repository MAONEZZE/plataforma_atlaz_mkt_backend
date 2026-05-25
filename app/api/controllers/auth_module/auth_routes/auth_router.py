# Merged from: contexts/auth/presentation/router.py + contexts/auth/presentation/deps.py
from fastapi import APIRouter, Depends, Request, Response
from supabase import Client
from supabase_auth.errors import AuthApiError

from app.api.config.dependencies.auth_deps import get_current_user
from app.api.config.rate_limiter import limiter
from app.api.controllers.auth_module.auth_dto.auth_dto import (
    LoginBody,
    LoginInput,
    TokensDTO,
    TokensResponse,
)
from app.database.shared.supabase_client import (
    create_supabase_admin_client,
    create_supabase_anon_client,
)
from app.domain.auth_module.auth_exceptions import InvalidCredentials, LogoutFailed
from app.domain.auth_module.auth_model import User as AuthUser
from app.domain.shared.base_exceptions import AppException
from app.services.auth_module.login_service import Login
from app.services.auth_module.logout_service import Logout


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


# ── FastAPI dependency factories ───────────────────────────────────────────────


def get_login_use_case() -> Login:
    gateway = SupabaseAuthGatewayImpl(
        anon_client=create_supabase_anon_client(),
        admin_client=create_supabase_admin_client(),
    )
    return Login(gateway=gateway)


def get_logout_use_case() -> Logout:
    gateway = SupabaseAuthGatewayImpl(
        anon_client=create_supabase_anon_client(),
        admin_client=create_supabase_admin_client(),
    )
    return Logout(gateway=gateway)


# ── Router ─────────────────────────────────────────────────────────────────────

router = APIRouter(prefix="/auth", tags=["auth"])


def _login() -> Login:
    return get_login_use_case()


def _logout() -> Logout:
    return get_logout_use_case()


@router.post("/login", response_model=TokensResponse)
@limiter.limit("5/minute")
async def login(
    request: Request,
    body: LoginBody,
    use_case: Login = Depends(_login),
) -> TokensResponse:
    try:
        tokens = await use_case.execute(LoginInput(email=body.email, password=body.password))
    except InvalidCredentials as exc:
        raise AppException("AUTH_FAILED", "Email ou senha inválidos.", 401) from exc
    return TokensResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        expires_in=tokens.expires_in,
        token_type=tokens.token_type,
    )


@router.post("/logout", status_code=204)
async def logout(
    request: Request,
    current_user: AuthUser = Depends(get_current_user),
    use_case: Logout = Depends(_logout),
) -> Response:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise AppException("INVALID_AUTH_HEADER", "Authorization header inválido.", 401)
    token = auth[7:]
    try:
        await use_case.execute(token)
    except LogoutFailed as exc:
        raise AppException("INTERNAL_ERROR", "Erro ao encerrar sessão.", 500) from exc
    return Response(status_code=204)
