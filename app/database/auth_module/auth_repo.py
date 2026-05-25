# Merged from: contexts/auth/infrastructure/models.py + contexts/auth/infrastructure/repositories.py
from uuid import UUID

from sqlalchemy import Boolean, String, select
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.database.shared.sqlalchemy_base import Base
from app.domain.auth_module.auth_model import User


class UserAuthModel(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "ATZ_HUB", "extend_existing": True}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    email: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)
    inactive: Mapped[bool] = mapped_column(Boolean, nullable=False)


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
