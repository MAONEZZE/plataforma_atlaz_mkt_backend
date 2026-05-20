import structlog
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.contexts.auth.application.use_cases.validate_token import ValidateToken
from app.contexts.auth.domain.entities import User
from app.contexts.auth.domain.exceptions import InactiveAccount, ExpiredToken, InvalidToken
from app.contexts.auth.presentation.deps import get_validate_token_use_case
from app.core.exceptions import AppException

http_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(http_bearer),
    use_case: ValidateToken = Depends(get_validate_token_use_case),
) -> User:
    token = credentials.credentials if credentials else None
    if not token:
        raise AppException("TOKEN_INVALID", "Token não fornecido.", 401)
    try:
        user = await use_case.execute(token)
        structlog.contextvars.bind_contextvars(user_id=str(user.id))
        return user
    except ExpiredToken as exc:
        raise AppException("TOKEN_EXPIRED", "Token expirado.", 401) from exc
    except InvalidToken as exc:
        raise AppException("TOKEN_INVALID", "Token inválido.", 401) from exc
    except InactiveAccount as exc:
        raise AppException("AUTH_INACTIVE_ACCOUNT", "Conta inativa.", 403) from exc


async def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise AppException("FORBIDDEN", "Apenas administradores.", 403)
    return user
