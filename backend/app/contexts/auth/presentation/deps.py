from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.contexts.auth.application.use_cases.login import Login
from app.contexts.auth.application.use_cases.logout import Logout
from app.contexts.auth.application.use_cases.validate_token import ValidarToken
from app.contexts.auth.infrastructure.jwt_decoder import decode_supabase_jwt
from app.contexts.auth.infrastructure.repositories import SqlAlchemyUserAuthRepository
from app.contexts.auth.infrastructure.supabase_auth_gateway import SupabaseAuthGatewayImpl
from app.core.db import get_session
from app.shared.infrastructure.supabase_client import (
    create_supabase_admin_client,
    create_supabase_anon_client,
)


def get_validar_token_use_case(
    session: AsyncSession = Depends(get_session),
) -> ValidarToken:
    repo = SqlAlchemyUserAuthRepository(session)
    return ValidarToken(repo=repo, jwt_decoder=decode_supabase_jwt)


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
