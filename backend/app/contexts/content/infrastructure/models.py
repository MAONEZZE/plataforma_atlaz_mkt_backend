from datetime import datetime
from uuid import UUID

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.infrastructure.sqlalchemy_base import Base


class TrackModel(Base):
    __tablename__ = "tracks"
    __table_args__ = {"schema": "public", "extend_existing": True}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    titulo: Mapped[str] = mapped_column(Text, nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text, nullable=True)
    capa_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    ordem: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    criado_em: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)


class ModuleModel(Base):
    __tablename__ = "modules"
    __table_args__ = {"schema": "public", "extend_existing": True}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    trilha_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("public.tracks.id", ondelete="CASCADE"),
        nullable=False,
    )
    titulo: Mapped[str] = mapped_column(Text, nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text, nullable=True)
    ordem: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class LessonModel(Base):
    __tablename__ = "lessons"
    __table_args__ = {"schema": "public", "extend_existing": True}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    modulo_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("public.modules.id", ondelete="CASCADE"),
        nullable=False,
    )
    titulo: Mapped[str] = mapped_column(Text, nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text, nullable=True)
    drive_file_id: Mapped[str] = mapped_column(Text, nullable=False)
    duracao_minutos: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ordem: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    criado_em: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)


class StudentLessonModel(Base):
    __tablename__ = "student_lessons"
    __table_args__ = (
        UniqueConstraint("usuario_id", "aula_id"),
        {"schema": "public", "extend_existing": True},
    )

    usuario_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("public.users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    aula_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("public.lessons.id", ondelete="CASCADE"),
        primary_key=True,
    )
    concluida_em: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)


class CommentModel(Base):
    __tablename__ = "comments"
    __table_args__ = {"schema": "public", "extend_existing": True}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    aula_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("public.lessons.id", ondelete="CASCADE"),
        nullable=False,
    )
    usuario_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("public.users.id", ondelete="CASCADE"),
        nullable=False,
    )
    texto: Mapped[str] = mapped_column(Text, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)
    editado_em: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True)
    apagado_em: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True)


class UserContentModel(Base):
    """Read-only view of public.usuario fields needed by the conteudo context."""

    __tablename__ = "users"
    __table_args__ = {"schema": "public", "extend_existing": True}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    nome: Mapped[str] = mapped_column(String, nullable=False)
    foto_url: Mapped[str | None] = mapped_column(String, nullable=True)
