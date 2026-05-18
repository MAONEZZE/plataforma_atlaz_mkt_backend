from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.utils import now_sp

from app.contexts.conteudo.domain.entities import (
    Aula,
    Comentario,
    ComentarioLeitura,
    Modulo,
    Trilha,
)
from app.contexts.conteudo.infrastructure.models import (
    AlunoAulaModel,
    AulaModel,
    ComentarioModel,
    ModuloModel,
    TrilhaModel,
    UsuarioConteudoModel,
)


def _trilha_from_model(m: TrilhaModel) -> Trilha:
    return Trilha(
        id=m.id,
        titulo=m.titulo,
        descricao=m.descricao,
        capa_url=m.capa_url,
        ordem=m.ordem,
        criado_em=m.criado_em,
    )


def _modulo_from_model(m: ModuloModel) -> Modulo:
    return Modulo(
        id=m.id,
        trilha_id=m.trilha_id,
        titulo=m.titulo,
        descricao=m.descricao,
        ordem=m.ordem,
    )


def _aula_from_model(m: AulaModel) -> Aula:
    return Aula(
        id=m.id,
        modulo_id=m.modulo_id,
        titulo=m.titulo,
        descricao=m.descricao,
        drive_file_id=m.drive_file_id,
        duracao_minutos=m.duracao_minutos,
        ordem=m.ordem,
        criado_em=m.criado_em,
    )


def _comentario_from_model(m: ComentarioModel) -> Comentario:
    return Comentario(
        id=m.id,
        aula_id=m.aula_id,
        usuario_id=m.usuario_id,
        texto=m.texto,
        criado_em=m.criado_em,
        editado_em=m.editado_em,
        apagado_em=m.apagado_em,
    )


class SqlAlchemyTrilhaRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def listar(self) -> list[Trilha]:
        result = await self._session.execute(
            select(TrilhaModel).order_by(TrilhaModel.ordem, TrilhaModel.criado_em)
        )
        return [_trilha_from_model(m) for m in result.scalars()]

    async def por_id(self, trilha_id: UUID) -> Trilha | None:
        result = await self._session.execute(
            select(TrilhaModel).where(TrilhaModel.id == trilha_id)
        )
        m = result.scalar_one_or_none()
        return _trilha_from_model(m) if m else None

    async def criar(self, trilha: Trilha) -> Trilha:
        model = TrilhaModel(
            id=trilha.id,
            titulo=trilha.titulo,
            descricao=trilha.descricao,
            capa_url=trilha.capa_url,
            ordem=trilha.ordem,
            criado_em=trilha.criado_em,
        )
        self._session.add(model)
        await self._session.flush()
        return trilha

    async def atualizar(self, trilha: Trilha) -> Trilha:
        await self._session.execute(
            update(TrilhaModel)
            .where(TrilhaModel.id == trilha.id)
            .values(
                titulo=trilha.titulo,
                descricao=trilha.descricao,
                capa_url=trilha.capa_url,
                ordem=trilha.ordem,
            )
        )
        return trilha

    async def remover(self, trilha_id: UUID) -> None:
        await self._session.execute(delete(TrilhaModel).where(TrilhaModel.id == trilha_id))

    async def reordenar(self, ordens: list[tuple[UUID, int]]) -> None:
        for trilha_id, ordem in ordens:
            await self._session.execute(
                update(TrilhaModel).where(TrilhaModel.id == trilha_id).values(ordem=ordem)
            )

    async def contar_aulas(self, trilha_id: UUID) -> int:
        result = await self._session.execute(
            select(AulaModel)
            .join(ModuloModel, AulaModel.modulo_id == ModuloModel.id)
            .where(ModuloModel.trilha_id == trilha_id)
        )
        return len(result.scalars().all())


class SqlAlchemyModuloRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def listar_por_trilha(self, trilha_id: UUID) -> list[Modulo]:
        result = await self._session.execute(
            select(ModuloModel)
            .where(ModuloModel.trilha_id == trilha_id)
            .order_by(ModuloModel.ordem)
        )
        return [_modulo_from_model(m) for m in result.scalars()]

    async def por_id(self, modulo_id: UUID) -> Modulo | None:
        result = await self._session.execute(
            select(ModuloModel).where(ModuloModel.id == modulo_id)
        )
        m = result.scalar_one_or_none()
        return _modulo_from_model(m) if m else None

    async def criar(self, modulo: Modulo) -> Modulo:
        model = ModuloModel(
            id=modulo.id,
            trilha_id=modulo.trilha_id,
            titulo=modulo.titulo,
            descricao=modulo.descricao,
            ordem=modulo.ordem,
        )
        self._session.add(model)
        await self._session.flush()
        return modulo

    async def atualizar(self, modulo: Modulo) -> Modulo:
        await self._session.execute(
            update(ModuloModel)
            .where(ModuloModel.id == modulo.id)
            .values(
                titulo=modulo.titulo,
                descricao=modulo.descricao,
                ordem=modulo.ordem,
            )
        )
        return modulo

    async def remover(self, modulo_id: UUID) -> None:
        await self._session.execute(delete(ModuloModel).where(ModuloModel.id == modulo_id))

    async def reordenar(self, ordens: list[tuple[UUID, int]]) -> None:
        for modulo_id, ordem in ordens:
            await self._session.execute(
                update(ModuloModel).where(ModuloModel.id == modulo_id).values(ordem=ordem)
            )


class SqlAlchemyAulaRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def por_id(self, aula_id: UUID) -> Aula | None:
        result = await self._session.execute(select(AulaModel).where(AulaModel.id == aula_id))
        m = result.scalar_one_or_none()
        return _aula_from_model(m) if m else None

    async def listar_por_modulo(self, modulo_id: UUID) -> list[Aula]:
        result = await self._session.execute(
            select(AulaModel).where(AulaModel.modulo_id == modulo_id).order_by(AulaModel.ordem)
        )
        return [_aula_from_model(m) for m in result.scalars()]

    async def criar(self, aula: Aula) -> Aula:
        model = AulaModel(
            id=aula.id,
            modulo_id=aula.modulo_id,
            titulo=aula.titulo,
            descricao=aula.descricao,
            drive_file_id=aula.drive_file_id,
            duracao_minutos=aula.duracao_minutos,
            ordem=aula.ordem,
            criado_em=aula.criado_em,
        )
        self._session.add(model)
        await self._session.flush()
        return aula

    async def atualizar(self, aula: Aula) -> Aula:
        await self._session.execute(
            update(AulaModel)
            .where(AulaModel.id == aula.id)
            .values(
                titulo=aula.titulo,
                descricao=aula.descricao,
                drive_file_id=aula.drive_file_id,
                duracao_minutos=aula.duracao_minutos,
                ordem=aula.ordem,
            )
        )
        return aula

    async def remover(self, aula_id: UUID) -> None:
        await self._session.execute(delete(AulaModel).where(AulaModel.id == aula_id))

    async def reordenar(self, ordens: list[tuple[UUID, int]]) -> None:
        for aula_id, ordem in ordens:
            await self._session.execute(
                update(AulaModel).where(AulaModel.id == aula_id).values(ordem=ordem)
            )

    async def proxima(self, aula: Aula) -> Aula | None:
        # Next in same modulo
        result = await self._session.execute(
            select(AulaModel)
            .where(AulaModel.modulo_id == aula.modulo_id, AulaModel.ordem > aula.ordem)
            .order_by(AulaModel.ordem)
            .limit(1)
        )
        next_model = result.scalar_one_or_none()
        if next_model:
            return _aula_from_model(next_model)

        # First aula of next modulo (by ordem)
        modulo_result = await self._session.execute(
            select(ModuloModel).where(ModuloModel.id == aula.modulo_id)
        )
        modulo = modulo_result.scalar_one_or_none()
        if modulo is None:
            return None

        next_modulo_result = await self._session.execute(
            select(ModuloModel)
            .where(
                ModuloModel.trilha_id == modulo.trilha_id,
                ModuloModel.ordem > modulo.ordem,
            )
            .order_by(ModuloModel.ordem)
            .limit(1)
        )
        next_modulo = next_modulo_result.scalar_one_or_none()
        if next_modulo is None:
            return None

        first_result = await self._session.execute(
            select(AulaModel)
            .where(AulaModel.modulo_id == next_modulo.id)
            .order_by(AulaModel.ordem)
            .limit(1)
        )
        first = first_result.scalar_one_or_none()
        return _aula_from_model(first) if first else None


class SqlAlchemyAlunoAulaRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def marcar_concluida(self, usuario_id: UUID, aula_id: UUID) -> None:
        existing = await self._session.execute(
            select(AlunoAulaModel).where(
                AlunoAulaModel.usuario_id == usuario_id,
                AlunoAulaModel.aula_id == aula_id,
            )
        )
        if existing.scalar_one_or_none() is None:
            self._session.add(
                AlunoAulaModel(
                    usuario_id=usuario_id,
                    aula_id=aula_id,
                    concluida_em=now_sp(),
                )
            )
            await self._session.flush()

    async def desmarcar(self, usuario_id: UUID, aula_id: UUID) -> None:
        await self._session.execute(
            delete(AlunoAulaModel).where(
                AlunoAulaModel.usuario_id == usuario_id,
                AlunoAulaModel.aula_id == aula_id,
            )
        )

    async def concluidas_ids(self, usuario_id: UUID) -> set[UUID]:
        result = await self._session.execute(
            select(AlunoAulaModel.aula_id).where(AlunoAulaModel.usuario_id == usuario_id)
        )
        return set(result.scalars())


class SqlAlchemyComentarioRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def listar_por_aula(
        self, aula_id: UUID, page: int, page_size: int
    ) -> tuple[list[ComentarioLeitura], int]:
        count_result = await self._session.execute(
            select(ComentarioModel).where(ComentarioModel.aula_id == aula_id)
        )
        total = len(count_result.scalars().all())

        offset = (page - 1) * page_size
        result = await self._session.execute(
            select(ComentarioModel, UsuarioConteudoModel)
            .join(UsuarioConteudoModel, ComentarioModel.usuario_id == UsuarioConteudoModel.id)
            .where(ComentarioModel.aula_id == aula_id)
            .order_by(ComentarioModel.criado_em.desc())
            .offset(offset)
            .limit(page_size)
        )
        rows = result.all()
        items = [
            ComentarioLeitura(
                id=c.id,
                aula_id=c.aula_id,
                usuario_id=c.usuario_id,
                texto=None if c.apagado_em else c.texto,
                criado_em=c.criado_em,
                editado_em=c.editado_em,
                apagado_em=c.apagado_em,
                autor_nome=u.nome,
                autor_foto_url=u.foto_url,
            )
            for c, u in rows
        ]
        return items, total

    async def por_id(self, comentario_id: UUID) -> Comentario | None:
        result = await self._session.execute(
            select(ComentarioModel).where(ComentarioModel.id == comentario_id)
        )
        m = result.scalar_one_or_none()
        return _comentario_from_model(m) if m else None

    async def criar(self, comentario: Comentario) -> Comentario:
        model = ComentarioModel(
            id=comentario.id,
            aula_id=comentario.aula_id,
            usuario_id=comentario.usuario_id,
            texto=comentario.texto,
            criado_em=comentario.criado_em,
            editado_em=comentario.editado_em,
            apagado_em=comentario.apagado_em,
        )
        self._session.add(model)
        await self._session.flush()
        return comentario

    async def atualizar(self, comentario: Comentario) -> Comentario:
        await self._session.execute(
            update(ComentarioModel)
            .where(ComentarioModel.id == comentario.id)
            .values(
                texto=comentario.texto,
                editado_em=comentario.editado_em,
                apagado_em=comentario.apagado_em,
            )
        )
        return comentario

    async def apagar(self, comentario_id: UUID) -> None:
        await self._session.execute(
            update(ComentarioModel)
            .where(ComentarioModel.id == comentario_id)
            .values(apagado_em=now_sp())
        )
