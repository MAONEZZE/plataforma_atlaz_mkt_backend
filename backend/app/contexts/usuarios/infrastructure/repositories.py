from uuid import UUID

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.contexts.usuarios.domain.entities import Usuario
from app.contexts.usuarios.infrastructure.models import UsuarioModel
from app.shared.utils import now_sp


class SqlAlchemyUsuarioRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def por_id(self, user_id: UUID) -> Usuario | None:
        result = await self._session.execute(
            select(UsuarioModel).where(UsuarioModel.id == user_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_entity(model)

    async def atualizar(self, usuario: Usuario) -> Usuario:
        now = now_sp()
        await self._session.execute(
            update(UsuarioModel)
            .where(UsuarioModel.id == usuario.id)
            .values(
                nome=usuario.nome,
                telefone=usuario.telefone,
                linkedin_url=usuario.linkedin_url,
                instagram_username=usuario.instagram_username,
                descricao=usuario.descricao,
                foto_url=usuario.foto_url,
                atualizado_em=now,
            )
        )
        usuario.atualizado_em = now
        return usuario

    @staticmethod
    def _to_entity(model: UsuarioModel) -> Usuario:
        return Usuario(
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
