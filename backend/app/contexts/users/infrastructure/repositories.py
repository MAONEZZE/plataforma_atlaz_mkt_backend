from uuid import UUID

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.contexts.users.domain.entities import User
from app.contexts.users.infrastructure.models import UserModel
from app.shared.utils import now_sp


class SqlAlchemyUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: UUID) -> User | None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_entity(model)

    async def update(self, user: User) -> User:
        now = now_sp()
        await self._session.execute(
            update(UserModel)
            .where(UserModel.id == user.id)
            .values(
                name=user.name,
                telefone=user.phone,
                linkedin_url=user.linkedin_url,
                instagram_username=user.instagram_username,
                description=user.description,
                photo_url=user.photo_url,
                updated_at=now,
            )
        )
        user.updated_at = now
        return user

    @staticmethod
    def _to_entity(model: UserModel) -> User:
        return User(
            id=model.id,
            name=model.name,
            email=model.email,
            phone=model.telefone,
            linkedin_url=model.linkedin_url,
            instagram_username=model.instagram_username,
            description=model.description,
            photo_url=model.photo_url,
            role=model.role,
            inactive=model.inactive,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
