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
        UniqueConstraint("user_id", "week_start"),
        {"schema": "public", "extend_existing": True},
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("public.users.id", ondelete="CASCADE"),
        nullable=False,
    )
    week_start: Mapped[date] = mapped_column(Date, nullable=False)
    calls_scheduled: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    calls_made: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    meetings_scheduled: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    referrals: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)


class UserMetricModel(Base):
    """Read-only view of public.users fields used by the metrics context."""

    __tablename__ = "users"
    __table_args__ = {"schema": "public", "extend_existing": True}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    photo_url: Mapped[str | None] = mapped_column(String, nullable=True)
    role: Mapped[str] = mapped_column(String, nullable=False)
    inactive: Mapped[bool] = mapped_column(Boolean, nullable=False)
