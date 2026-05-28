from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UniqueConstraint, delete, select, update
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.database.shared.sqlalchemy_base import Base
from app.domain.content_module.content_model import (
    Comment,
    CommentRead,
    Lesson,
    Module,
    Track,
)
from app.domain.shared.utils import now_sp


class TrackModel(Base):
    __tablename__ = "tracks"
    __table_args__ = {"schema": "ATZ_HUB", "extend_existing": True}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    title: Mapped[str] = mapped_column("titulo", Text, nullable=False)
    description: Mapped[str | None] = mapped_column("descricao", Text, nullable=True)
    cover_url: Mapped[str | None] = mapped_column("capa_url", Text, nullable=True)
    order: Mapped[int] = mapped_column("ordem", Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)


class ModuleModel(Base):
    __tablename__ = "modules"
    __table_args__ = {"schema": "ATZ_HUB", "extend_existing": True}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    track_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("ATZ_HUB.tracks.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column("titulo", Text, nullable=False)
    description: Mapped[str | None] = mapped_column("descricao", Text, nullable=True)
    order: Mapped[int] = mapped_column("ordem", Integer, nullable=False, default=0)


class LessonModel(Base):
    __tablename__ = "lessons"
    __table_args__ = {"schema": "ATZ_HUB", "extend_existing": True}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    module_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("ATZ_HUB.modules.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column("titulo", Text, nullable=False)
    description: Mapped[str | None] = mapped_column("descricao", Text, nullable=True)
    drive_file_id: Mapped[str] = mapped_column(Text, nullable=False)
    duration_minutes: Mapped[int | None] = mapped_column("duracao_minutos", Integer, nullable=True)
    order: Mapped[int] = mapped_column("ordem", Integer, nullable=False, default=0)
    is_doc: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)


class StudentLessonModel(Base):
    __tablename__ = "student_lessons"
    __table_args__ = (
        UniqueConstraint("user_id", "lesson_id"),
        {"schema": "ATZ_HUB", "extend_existing": True},
    )

    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("ATZ_HUB.users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    lesson_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("ATZ_HUB.lessons.id", ondelete="CASCADE"),
        primary_key=True,
    )
    completed_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)


class CommentModel(Base):
    __tablename__ = "comments"
    __table_args__ = {"schema": "ATZ_HUB", "extend_existing": True}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    lesson_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("ATZ_HUB.lessons.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("ATZ_HUB.users.id", ondelete="CASCADE"),
        nullable=False,
    )
    text: Mapped[str] = mapped_column("texto", Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)
    edited_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True)


class UserContentModel(Base):
    """Read-only view of public.users fields needed by the content context."""

    __tablename__ = "users"
    __table_args__ = {"schema": "ATZ_HUB", "extend_existing": True}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    photo_url: Mapped[str | None] = mapped_column(String, nullable=True)


def _track_from_model(m: TrackModel) -> Track:
    return Track(
        id=m.id,
        title=m.title,
        description=m.description,
        cover_url=m.cover_url,
        order=m.order,
        created_at=m.created_at,
    )


def _module_from_model(m: ModuleModel) -> Module:
    return Module(
        id=m.id,
        track_id=m.track_id,
        title=m.title,
        description=m.description,
        order=m.order,
    )


def _lesson_from_model(m: LessonModel) -> Lesson:
    return Lesson(
        id=m.id,
        module_id=m.module_id,
        title=m.title,
        description=m.description,
        drive_file_id=m.drive_file_id,
        duration_minutes=m.duration_minutes,
        order=m.order,
        is_doc=m.is_doc,
        created_at=m.created_at,
    )


def _comment_from_model(m: CommentModel) -> Comment:
    return Comment(
        id=m.id,
        lesson_id=m.lesson_id,
        user_id=m.user_id,
        text=m.text,
        created_at=m.created_at,
        edited_at=m.edited_at,
        deleted_at=m.deleted_at,
    )


class SqlAlchemyTrackRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_all(self) -> list[Track]:
        result = await self._session.execute(
            select(TrackModel).order_by(TrackModel.order, TrackModel.created_at)
        )
        return [_track_from_model(m) for m in result.scalars()]

    async def get_by_id(self, track_id: UUID) -> Track | None:
        result = await self._session.execute(
            select(TrackModel).where(TrackModel.id == track_id)
        )
        m = result.scalar_one_or_none()
        return _track_from_model(m) if m else None

    async def create(self, track: Track) -> Track:
        model = TrackModel(
            id=track.id,
            title=track.title,
            description=track.description,
            cover_url=track.cover_url,
            order=track.order,
            created_at=track.created_at,
        )
        self._session.add(model)
        await self._session.flush()
        return track

    async def update(self, track: Track) -> Track:
        await self._session.execute(
            update(TrackModel)
            .where(TrackModel.id == track.id)
            .values(
                title=track.title,
                description=track.description,
                cover_url=track.cover_url,
                order=track.order,
            )
        )
        return track

    async def delete(self, track_id: UUID) -> None:
        await self._session.execute(delete(TrackModel).where(TrackModel.id == track_id))

    async def reorder(self, orders: list[tuple[UUID, int]]) -> None:
        for track_id, order_val in orders:
            await self._session.execute(
                update(TrackModel).where(TrackModel.id == track_id).values(order=order_val)
            )

class SqlAlchemyModuleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_track(self, track_id: UUID) -> list[Module]:
        result = await self._session.execute(
            select(ModuleModel)
            .where(ModuleModel.track_id == track_id)
            .order_by(ModuleModel.order)
        )
        return [_module_from_model(m) for m in result.scalars()]

    async def get_by_id(self, module_id: UUID) -> Module | None:
        result = await self._session.execute(
            select(ModuleModel).where(ModuleModel.id == module_id)
        )
        m = result.scalar_one_or_none()
        return _module_from_model(m) if m else None

    async def create(self, module: Module) -> Module:
        model = ModuleModel(
            id=module.id,
            track_id=module.track_id,
            title=module.title,
            description=module.description,
            order=module.order,
        )
        self._session.add(model)
        await self._session.flush()
        return module

    async def update(self, module: Module) -> Module:
        await self._session.execute(
            update(ModuleModel)
            .where(ModuleModel.id == module.id)
            .values(
                title=module.title,
                description=module.description,
                order=module.order,
            )
        )
        return module

    async def delete(self, module_id: UUID) -> None:
        await self._session.execute(delete(ModuleModel).where(ModuleModel.id == module_id))

    async def reorder(self, orders: list[tuple[UUID, int]]) -> None:
        for module_id, order_val in orders:
            await self._session.execute(
                update(ModuleModel).where(ModuleModel.id == module_id).values(order=order_val)
            )


class SqlAlchemyLessonRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, lesson_id: UUID) -> Lesson | None:
        result = await self._session.execute(
            select(LessonModel).where(LessonModel.id == lesson_id)
        )
        m = result.scalar_one_or_none()
        return _lesson_from_model(m) if m else None

    async def list_by_module(self, module_id: UUID) -> list[Lesson]:
        result = await self._session.execute(
            select(LessonModel)
            .where(LessonModel.module_id == module_id)
            .order_by(LessonModel.order)
        )
        return [_lesson_from_model(m) for m in result.scalars()]

    async def create(self, lesson: Lesson) -> Lesson:
        model = LessonModel(
            id=lesson.id,
            module_id=lesson.module_id,
            title=lesson.title,
            description=lesson.description,
            drive_file_id=lesson.drive_file_id,
            duration_minutes=lesson.duration_minutes,
            order=lesson.order,
            is_doc=lesson.is_doc,
            created_at=lesson.created_at,
        )
        self._session.add(model)
        await self._session.flush()
        return lesson

    async def update(self, lesson: Lesson) -> Lesson:
        await self._session.execute(
            update(LessonModel)
            .where(LessonModel.id == lesson.id)
            .values(
                title=lesson.title,
                description=lesson.description,
                drive_file_id=lesson.drive_file_id,
                duration_minutes=lesson.duration_minutes,
                order=lesson.order,
                is_doc=lesson.is_doc,
            )
        )
        return lesson

    async def delete(self, lesson_id: UUID) -> None:
        await self._session.execute(delete(LessonModel).where(LessonModel.id == lesson_id))

    async def reorder(self, orders: list[tuple[UUID, int]]) -> None:
        for lesson_id, order_val in orders:
            await self._session.execute(
                update(LessonModel).where(LessonModel.id == lesson_id).values(order=order_val)
            )

    async def next_lesson(self, lesson: Lesson) -> Lesson | None:
        # Next in same module
        result = await self._session.execute(
            select(LessonModel)
            .where(LessonModel.module_id == lesson.module_id, LessonModel.order > lesson.order)
            .order_by(LessonModel.order)
            .limit(1)
        )
        next_model = result.scalar_one_or_none()
        if next_model:
            return _lesson_from_model(next_model)

        # First lesson of next module (by order)
        module_result = await self._session.execute(
            select(ModuleModel).where(ModuleModel.id == lesson.module_id)
        )
        module = module_result.scalar_one_or_none()
        if module is None:
            return None

        next_module_result = await self._session.execute(
            select(ModuleModel)
            .where(
                ModuleModel.track_id == module.track_id,
                ModuleModel.order > module.order,
            )
            .order_by(ModuleModel.order)
            .limit(1)
        )
        next_module = next_module_result.scalar_one_or_none()
        if next_module is None:
            return None

        first_result = await self._session.execute(
            select(LessonModel)
            .where(LessonModel.module_id == next_module.id)
            .order_by(LessonModel.order)
            .limit(1)
        )
        first = first_result.scalar_one_or_none()
        return _lesson_from_model(first) if first else None


class SqlAlchemyStudentLessonRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def mark_completed(self, user_id: UUID, lesson_id: UUID) -> None:
        existing = await self._session.execute(
            select(StudentLessonModel).where(
                StudentLessonModel.user_id == user_id,
                StudentLessonModel.lesson_id == lesson_id,
            )
        )
        if existing.scalar_one_or_none() is None:
            self._session.add(
                StudentLessonModel(
                    user_id=user_id,
                    lesson_id=lesson_id,
                    completed_at=now_sp(),
                )
            )
            await self._session.flush()

    async def unmark(self, user_id: UUID, lesson_id: UUID) -> None:
        await self._session.execute(
            delete(StudentLessonModel).where(
                StudentLessonModel.user_id == user_id,
                StudentLessonModel.lesson_id == lesson_id,
            )
        )
        await self._session.flush()

    async def completed_ids(self, user_id: UUID) -> set[UUID]:
        result = await self._session.execute(
            select(StudentLessonModel.lesson_id).where(StudentLessonModel.user_id == user_id)
        )
        return set(result.scalars())


class SqlAlchemyCommentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_lesson(
        self, lesson_id: UUID, page: int, page_size: int
    ) -> tuple[list[CommentRead], int]:
        count_result = await self._session.execute(
            select(CommentModel).where(CommentModel.lesson_id == lesson_id)
        )
        total = len(count_result.scalars().all())

        offset = (page - 1) * page_size
        result = await self._session.execute(
            select(CommentModel, UserContentModel)
            .join(UserContentModel, CommentModel.user_id == UserContentModel.id)
            .where(CommentModel.lesson_id == lesson_id)
            .order_by(CommentModel.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        rows = result.all()
        items = [
            CommentRead(
                id=c.id,
                lesson_id=c.lesson_id,
                user_id=c.user_id,
                text=None if c.deleted_at else c.text,
                created_at=c.created_at,
                edited_at=c.edited_at,
                deleted_at=c.deleted_at,
                author_name=u.name,
                author_photo_url=u.photo_url,
            )
            for c, u in rows
        ]
        return items, total

    async def get_by_id(self, comment_id: UUID) -> Comment | None:
        result = await self._session.execute(
            select(CommentModel).where(CommentModel.id == comment_id)
        )
        m = result.scalar_one_or_none()
        return _comment_from_model(m) if m else None

    async def create(self, comment: Comment) -> Comment:
        model = CommentModel(
            id=comment.id,
            lesson_id=comment.lesson_id,
            user_id=comment.user_id,
            text=comment.text,
            created_at=comment.created_at,
            edited_at=comment.edited_at,
            deleted_at=comment.deleted_at,
        )
        self._session.add(model)
        await self._session.flush()
        return comment

    async def update(self, comment: Comment) -> Comment:
        await self._session.execute(
            update(CommentModel)
            .where(CommentModel.id == comment.id)
            .values(
                text=comment.text,
                edited_at=comment.edited_at,
                deleted_at=comment.deleted_at,
            )
        )
        return comment

    async def delete_comment(self, comment_id: UUID) -> None:
        await self._session.execute(
            update(CommentModel)
            .where(CommentModel.id == comment_id)
            .values(deleted_at=now_sp())
        )
