from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, String, Text, update
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import Mapped, mapped_column

from app.database.shared.sqlalchemy_base import Base
from app.domain.shared.utils import now_sp
from app.domain.user_module.user_model import User


class UserModel(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "ATZ_HUB", "extend_existing": True}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False)
    telefone: Mapped[str | None] = mapped_column(String, nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String, nullable=True)
    instagram_username: Mapped[str | None] = mapped_column(String, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    photo_url: Mapped[str | None] = mapped_column(String, nullable=True)
    role: Mapped[str] = mapped_column(String, nullable=False)
    inactive: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


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
