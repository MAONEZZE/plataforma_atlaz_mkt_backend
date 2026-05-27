from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, String, Text, func, update
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.dialects.postgresql import insert
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

    async def upsert_new(self, user: User) -> None:
        """Insert a new user row, no-op if id already exists (trigger may
        have already created it). Required for environments where the
        auth.users → ATZ_HUB.users trigger is absent or disabled."""
        stmt = insert(UserModel).values(
            id=user.id,
            name=user.name,
            email=user.email,
            telefone=user.phone,
            linkedin_url=user.linkedin_url,
            instagram_username=user.instagram_username,
            description=user.description,
            photo_url=user.photo_url,
            role=user.role,
            inactive=user.inactive,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
        stmt = stmt.on_conflict_do_nothing(index_elements=["id"])
        await self._session.execute(stmt)

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

    async def list_clients(
        self, page: int, page_size: int
    ) -> tuple[list[User], int]:
        offset = (page - 1) * page_size
        base_filter = (UserModel.role == "cliente") & (UserModel.inactive.is_(False))

        rows = await self._session.execute(
            select(UserModel)
            .where(base_filter)
            .order_by(UserModel.created_at.desc())
            .limit(page_size)
            .offset(offset)
        )
        items = [self._to_entity(m) for m in rows.scalars().all()]

        total_res = await self._session.execute(
            select(func.count()).select_from(UserModel).where(base_filter)
        )
        total = int(total_res.scalar_one())
        return items, total

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
