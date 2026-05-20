from uuid import UUID

from sqlalchemy import Boolean, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.infrastructure.sqlalchemy_base import Base


class UserAuthModel(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "public", "extend_existing": True}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    email: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)
    inativo: Mapped[bool] = mapped_column(Boolean, nullable=False)
