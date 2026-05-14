from dataclasses import dataclass
from uuid import UUID

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.exceptions import AppException
from app.core.security import decode_supabase_jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)


@dataclass
class AuthUser:
    id: UUID
    email: str
    role: str
    inativo: bool


async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
) -> AuthUser:
    if not token:
        raise AppException("TOKEN_INVALID", "Token não fornecido.", 401)
    payload = decode_supabase_jwt(token)
    user_id = UUID(str(payload["sub"]))
    result = await session.execute(
        text("SELECT id, email, role, inativo FROM public.usuario WHERE id = :id"),
        {"id": user_id},
    )
    row = result.fetchone()
    if not row:
        raise AppException("TOKEN_INVALID", "Usuário não encontrado.", 401)
    if row.inativo:
        raise AppException("AUTH_INACTIVE_ACCOUNT", "Conta inativa.", 403)
    return AuthUser(id=row.id, email=row.email, role=row.role, inativo=row.inativo)


async def require_admin(
    user: AuthUser = Depends(get_current_user),
) -> AuthUser:
    if user.role != "admin":
        raise AppException("FORBIDDEN", "Apenas administradores.", 403)
    return user
