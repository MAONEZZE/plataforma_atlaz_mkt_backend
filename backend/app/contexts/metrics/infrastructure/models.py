from datetime import date, datetime
from uuid import UUID

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.infrastructure.sqlalchemy_base import Base


class WeeklyMetricModel(Base):
    __tablename__ = "weekly_metrics"
    __table_args__ = (
        UniqueConstraint("usuario_id", "semana_inicio"),
        {"schema": "public", "extend_existing": True},
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    usuario_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("public.users.id", ondelete="CASCADE"),
        nullable=False,
    )
    semana_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    ligacoes_agendadas: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ligacoes_realizadas: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reunioes_agendadas: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    indicacoes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    criado_em: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)
    atualizado_em: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)


class UserMetricModel(Base):
    """Read-only view of public.usuario fields used by the metricas context."""

    __tablename__ = "users"
    __table_args__ = {"schema": "public", "extend_existing": True}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    nome: Mapped[str] = mapped_column(String, nullable=False)
    foto_url: Mapped[str | None] = mapped_column(String, nullable=True)
    role: Mapped[str] = mapped_column(String, nullable=False)
    inativo: Mapped[bool] = mapped_column(Boolean, nullable=False)
