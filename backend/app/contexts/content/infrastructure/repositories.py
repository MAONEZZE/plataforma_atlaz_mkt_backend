from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.utils import now_sp

from app.contexts.content.domain.entities import (
    Lesson,
    Comment,
    CommentRead,
    Module,
    Track,
)
from app.contexts.content.infrastructure.models import (
    StudentLessonModel,
    LessonModel,
    CommentModel,
    ModuleModel,
    TrackModel,
    UserContentModel,
)


def _track_from_model(m: TrackModel) -> Track:
    return Track(
        id=m.id,
        titulo=m.titulo,
        descricao=m.descricao,
        capa_url=m.capa_url,
        ordem=m.ordem,
        criado_em=m.criado_em,
    )


def _module_from_model(m: ModuleModel) -> Module:
    return Module(
        id=m.id,
        trilha_id=m.trilha_id,
        titulo=m.titulo,
        descricao=m.descricao,
        ordem=m.ordem,
    )


def _lesson_from_model(m: LessonModel) -> Lesson:
    return Lesson(
        id=m.id,
        modulo_id=m.modulo_id,
        titulo=m.titulo,
        descricao=m.descricao,
        drive_file_id=m.drive_file_id,
        duracao_minutos=m.duracao_minutos,
        ordem=m.ordem,
        criado_em=m.criado_em,
    )


def _comment_from_model(m: CommentModel) -> Comment:
    return Comment(
        id=m.id,
        aula_id=m.aula_id,
        usuario_id=m.usuario_id,
        texto=m.texto,
        criado_em=m.criado_em,
        editado_em=m.editado_em,
        apagado_em=m.apagado_em,
    )


class SqlAlchemyTrackRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_all(self) -> list[Track]:
        result = await self._session.execute(
            select(TrackModel).order_by(TrackModel.ordem, TrackModel.criado_em)
        )
        return [_track_from_model(m) for m in result.scalars()]

    async def get_by_id(self, trilha_id: UUID) -> Track | None:
        result = await self._session.execute(
            select(TrackModel).where(TrackModel.id == trilha_id)
        )
        m = result.scalar_one_or_none()
        return _track_from_model(m) if m else None

    async def create(self, trilha: Track) -> Track:
        model = TrackModel(
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

    async def update(self, trilha: Track) -> Track:
        await self._session.execute(
            update(TrackModel)
            .where(TrackModel.id == trilha.id)
            .values(
                titulo=trilha.titulo,
                descricao=trilha.descricao,
                capa_url=trilha.capa_url,
                ordem=trilha.ordem,
            )
        )
        return trilha

    async def delete(self, trilha_id: UUID) -> None:
        await self._session.execute(delete(TrackModel).where(TrackModel.id == trilha_id))

    async def reorder(self, ordens: list[tuple[UUID, int]]) -> None:
        for trilha_id, ordem in ordens:
            await self._session.execute(
                update(TrackModel).where(TrackModel.id == trilha_id).values(ordem=ordem)
            )

    async def count_lessons(self, trilha_id: UUID) -> int:
        result = await self._session.execute(
            select(LessonModel)
            .join(ModuleModel, LessonModel.modulo_id == ModuleModel.id)
            .where(ModuleModel.trilha_id == trilha_id)
        )
        return len(result.scalars().all())


class SqlAlchemyModuleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_track(self, trilha_id: UUID) -> list[Module]:
        result = await self._session.execute(
            select(ModuleModel)
            .where(ModuleModel.trilha_id == trilha_id)
            .order_by(ModuleModel.ordem)
        )
        return [_module_from_model(m) for m in result.scalars()]

    async def get_by_id(self, modulo_id: UUID) -> Module | None:
        result = await self._session.execute(
            select(ModuleModel).where(ModuleModel.id == modulo_id)
        )
        m = result.scalar_one_or_none()
        return _module_from_model(m) if m else None

    async def create(self, modulo: Module) -> Module:
        model = ModuleModel(
            id=modulo.id,
            trilha_id=modulo.trilha_id,
            titulo=modulo.titulo,
            descricao=modulo.descricao,
            ordem=modulo.ordem,
        )
        self._session.add(model)
        await self._session.flush()
        return modulo

    async def update(self, modulo: Module) -> Module:
        await self._session.execute(
            update(ModuleModel)
            .where(ModuleModel.id == modulo.id)
            .values(
                titulo=modulo.titulo,
                descricao=modulo.descricao,
                ordem=modulo.ordem,
            )
        )
        return modulo

    async def delete(self, modulo_id: UUID) -> None:
        await self._session.execute(delete(ModuleModel).where(ModuleModel.id == modulo_id))

    async def reorder(self, ordens: list[tuple[UUID, int]]) -> None:
        for modulo_id, ordem in ordens:
            await self._session.execute(
                update(ModuleModel).where(ModuleModel.id == modulo_id).values(ordem=ordem)
            )


class SqlAlchemyLessonRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, aula_id: UUID) -> Lesson | None:
        result = await self._session.execute(select(LessonModel).where(LessonModel.id == aula_id))
        m = result.scalar_one_or_none()
        return _lesson_from_model(m) if m else None

    async def list_by_module(self, modulo_id: UUID) -> list[Lesson]:
        result = await self._session.execute(
            select(LessonModel).where(LessonModel.modulo_id == modulo_id).order_by(LessonModel.ordem)
        )
        return [_lesson_from_model(m) for m in result.scalars()]

    async def create(self, aula: Lesson) -> Lesson:
        model = LessonModel(
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

    async def update(self, aula: Lesson) -> Lesson:
        await self._session.execute(
            update(LessonModel)
            .where(LessonModel.id == aula.id)
            .values(
                titulo=aula.titulo,
                descricao=aula.descricao,
                drive_file_id=aula.drive_file_id,
                duracao_minutos=aula.duracao_minutos,
                ordem=aula.ordem,
            )
        )
        return aula

    async def delete(self, aula_id: UUID) -> None:
        await self._session.execute(delete(LessonModel).where(LessonModel.id == aula_id))

    async def reorder(self, ordens: list[tuple[UUID, int]]) -> None:
        for aula_id, ordem in ordens:
            await self._session.execute(
                update(LessonModel).where(LessonModel.id == aula_id).values(ordem=ordem)
            )

    async def next_lesson(self, aula: Lesson) -> Lesson | None:
        # Next in same modulo
        result = await self._session.execute(
            select(LessonModel)
            .where(LessonModel.modulo_id == aula.modulo_id, LessonModel.ordem > aula.ordem)
            .order_by(LessonModel.ordem)
            .limit(1)
        )
        next_model = result.scalar_one_or_none()
        if next_model:
            return _lesson_from_model(next_model)

        # First aula of next modulo (by ordem)
        modulo_result = await self._session.execute(
            select(ModuleModel).where(ModuleModel.id == aula.modulo_id)
        )
        modulo = modulo_result.scalar_one_or_none()
        if modulo is None:
            return None

        next_modulo_result = await self._session.execute(
            select(ModuleModel)
            .where(
                ModuleModel.trilha_id == modulo.trilha_id,
                ModuleModel.ordem > modulo.ordem,
            )
            .order_by(ModuleModel.ordem)
            .limit(1)
        )
        next_modulo = next_modulo_result.scalar_one_or_none()
        if next_modulo is None:
            return None

        first_result = await self._session.execute(
            select(LessonModel)
            .where(LessonModel.modulo_id == next_modulo.id)
            .order_by(LessonModel.ordem)
            .limit(1)
        )
        first = first_result.scalar_one_or_none()
        return _lesson_from_model(first) if first else None


class SqlAlchemyStudentLessonRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def mark_completed(self, usuario_id: UUID, aula_id: UUID) -> None:
        existing = await self._session.execute(
            select(StudentLessonModel).where(
                StudentLessonModel.usuario_id == usuario_id,
                StudentLessonModel.aula_id == aula_id,
            )
        )
        if existing.scalar_one_or_none() is None:
            self._session.add(
                StudentLessonModel(
                    usuario_id=usuario_id,
                    aula_id=aula_id,
                    concluida_em=now_sp(),
                )
            )
            await self._session.flush()

    async def unmark(self, usuario_id: UUID, aula_id: UUID) -> None:
        await self._session.execute(
            delete(StudentLessonModel).where(
                StudentLessonModel.usuario_id == usuario_id,
                StudentLessonModel.aula_id == aula_id,
            )
        )

    async def completed_ids(self, usuario_id: UUID) -> set[UUID]:
        result = await self._session.execute(
            select(StudentLessonModel.aula_id).where(StudentLessonModel.usuario_id == usuario_id)
        )
        return set(result.scalars())


class SqlAlchemyCommentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_lesson(
        self, aula_id: UUID, page: int, page_size: int
    ) -> tuple[list[CommentRead], int]:
        count_result = await self._session.execute(
            select(CommentModel).where(CommentModel.aula_id == aula_id)
        )
        total = len(count_result.scalars().all())

        offset = (page - 1) * page_size
        result = await self._session.execute(
            select(CommentModel, UserContentModel)
            .join(UserContentModel, CommentModel.usuario_id == UserContentModel.id)
            .where(CommentModel.aula_id == aula_id)
            .order_by(CommentModel.criado_em.desc())
            .offset(offset)
            .limit(page_size)
        )
        rows = result.all()
        items = [
            CommentRead(
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

    async def get_by_id(self, comentario_id: UUID) -> Comment | None:
        result = await self._session.execute(
            select(CommentModel).where(CommentModel.id == comentario_id)
        )
        m = result.scalar_one_or_none()
        return _comment_from_model(m) if m else None

    async def create(self, comentario: Comment) -> Comment:
        model = CommentModel(
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

    async def update(self, comentario: Comment) -> Comment:
        await self._session.execute(
            update(CommentModel)
            .where(CommentModel.id == comentario.id)
            .values(
                texto=comentario.texto,
                editado_em=comentario.editado_em,
                apagado_em=comentario.apagado_em,
            )
        )
        return comentario

    async def delete_comment(self, comentario_id: UUID) -> None:
        await self._session.execute(
            update(CommentModel)
            .where(CommentModel.id == comentario_id)
            .values(apagado_em=now_sp())
        )
