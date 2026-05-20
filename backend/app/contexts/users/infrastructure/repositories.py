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
                nome=user.nome,
                telefone=user.telefone,
                linkedin_url=user.linkedin_url,
                instagram_username=user.instagram_username,
                descricao=user.descricao,
                foto_url=user.foto_url,
                atualizado_em=now,
            )
        )
        user.atualizado_em = now
        return user

    @staticmethod
    def _to_entity(model: UserModel) -> User:
        return User(
            id=model.id,
            nome=model.nome,
            email=model.email,
            telefone=model.telefone,
            linkedin_url=model.linkedin_url,
            instagram_username=model.instagram_username,
            descricao=model.descricao,
            foto_url=model.foto_url,
            role=model.role,
            inativo=model.inativo,
            criado_em=model.criado_em,
            atualizado_em=model.atualizado_em,
        )
