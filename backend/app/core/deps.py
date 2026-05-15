import structlog
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.contexts.auth.application.use_cases.validar_token import ValidarToken
from app.contexts.auth.domain.entities import Usuario
from app.contexts.auth.domain.exceptions import ContaInativa, TokenExpirado, TokenInvalido
from app.contexts.auth.presentation.deps import get_validar_token_use_case
from app.core.exceptions import AppException

http_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(http_bearer),
    use_case: ValidarToken = Depends(get_validar_token_use_case),
) -> Usuario:
    token = credentials.credentials if credentials else None
    if not token:
        raise AppException("TOKEN_INVALID", "Token não fornecido.", 401)
    try:
        user = await use_case.execute(token)
        structlog.contextvars.bind_contextvars(usuario_id=str(user.id))
        return user
    except TokenExpirado as exc:
        raise AppException("TOKEN_EXPIRED", "Token expirado.", 401) from exc
    except TokenInvalido as exc:
        raise AppException("TOKEN_INVALID", "Token inválido.", 401) from exc
    except ContaInativa as exc:
        raise AppException("AUTH_INACTIVE_ACCOUNT", "Conta inativa.", 403) from exc


async def require_admin(user: Usuario = Depends(get_current_user)) -> Usuario:
    if user.role != "admin":
        raise AppException("FORBIDDEN", "Apenas administradores.", 403)
    return user
