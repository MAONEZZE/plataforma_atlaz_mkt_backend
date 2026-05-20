from fastapi import APIRouter, Depends, Request, Response

from app.contexts.auth.application.dtos import LoginInput
from app.contexts.auth.application.use_cases.login import Login
from app.contexts.auth.application.use_cases.logout import Logout
from app.contexts.auth.domain.entities import User as AuthUser
from app.contexts.auth.domain.exceptions import InvalidCredentials, LogoutFailed
from app.contexts.auth.presentation.deps import get_login_use_case, get_logout_use_case
from app.contexts.auth.presentation.schemas import LoginBody, TokensResponse
from app.core.deps import get_current_user
from app.core.exceptions import AppException
from app.core.rate_limit import limiter

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
    token = request.headers.get("Authorization", "")[len("Bearer "):]
    try:
        await use_case.execute(token)
    except LogoutFailed as exc:
        raise AppException("INTERNAL_ERROR", "Erro ao encerrar sessão.", 500) from exc
    return Response(status_code=204)
