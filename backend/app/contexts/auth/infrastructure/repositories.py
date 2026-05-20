from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.contexts.auth.domain.entities import User
from app.contexts.auth.infrastructure.models import UserAuthModel


class SqlAlchemyUserAuthRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: UUID) -> User | None:
        result = await self._session.execute(
            select(UserAuthModel).where(UserAuthModel.id == user_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return User(
            id=model.id,
            email=model.email,
            role=model.role,
            inactive=model.inactive,
        )
