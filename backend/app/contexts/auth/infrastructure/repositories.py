from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.contexts.auth.domain.entities import Usuario
from app.contexts.auth.infrastructure.models import UsuarioAuthModel


class SqlAlchemyUsuarioAuthRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def por_id(self, user_id: UUID) -> Usuario | None:
        result = await self._session.execute(
            select(UsuarioAuthModel).where(UsuarioAuthModel.id == user_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return Usuario(
            id=model.id,
            email=model.email,
            role=model.role,
            inativo=model.inativo,
        )
