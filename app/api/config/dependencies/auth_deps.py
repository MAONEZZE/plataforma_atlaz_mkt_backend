import structlog
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.auth_module.auth_repo import SqlAlchemyUserAuthRepository
from app.database.shared.db_factory import get_session
from app.domain.auth_module.auth_exceptions import ExpiredToken, InactiveAccount, InvalidToken
from app.domain.auth_module.auth_model import User
from app.domain.shared.base_exceptions import AppException
from app.services.auth_module.jwt_decoder import decode_supabase_jwt
from app.services.auth_module.validate_token_service import ValidateToken

http_bearer = HTTPBearer(auto_error=False)


def get_validate_token_use_case(
    session: AsyncSession = Depends(get_session),
) -> ValidateToken:
    repo = SqlAlchemyUserAuthRepository(session)
    return ValidateToken(repo=repo, jwt_decoder=decode_supabase_jwt)


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
