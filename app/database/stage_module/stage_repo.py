from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.database.shared.sqlalchemy_base import Base
from app.domain.shared.utils import now_sp
from app.domain.stage_module.stage_exceptions import StageAlreadyAttached, StageNotFound
from app.domain.stage_module.stage_model import Stage, UserStage


class StageModel(Base):
    __tablename__ = "stages"
    __table_args__ = {"schema": "ATZ_HUB", "extend_existing": True}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    text: Mapped[str] = mapped_column(sa.Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)


class UserStageModel(Base):
    __tablename__ = "user_stages"
    __table_args__ = {"schema": "ATZ_HUB", "extend_existing": True}

    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        sa.ForeignKey("ATZ_HUB.users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    stage_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        sa.ForeignKey("ATZ_HUB.stages.id", ondelete="CASCADE"),
        primary_key=True,
    )
    done: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=False)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)


def _stage_from(m: StageModel) -> Stage:
    return Stage(id=m.id, text=m.text, created_at=m.created_at)


def _user_stage_from(m: UserStageModel) -> UserStage:
    return UserStage(user_id=m.user_id, stage_id=m.stage_id, done=m.done, updated_at=m.updated_at)


class SqlAlchemyStageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, stage: Stage) -> Stage:
        model = StageModel(id=stage.id, text=stage.text, created_at=stage.created_at)
        self._session.add(model)
        await self._session.flush()
        return stage

    async def update(self, stage: Stage) -> Stage:
        await self._session.execute(
            sa.update(StageModel)
            .where(StageModel.id == stage.id)
            .values(text=stage.text)
        )
        return stage

    async def delete(self, stage_id: UUID) -> None:
        await self._session.execute(
            sa.delete(StageModel).where(StageModel.id == stage_id)
        )

    async def get_by_id(self, stage_id: UUID) -> Stage | None:
        result = await self._session.execute(
            sa.select(StageModel).where(StageModel.id == stage_id)
        )
        m = result.scalar_one_or_none()
        return _stage_from(m) if m else None

    async def list_all(self) -> list[Stage]:
        result = await self._session.execute(
            sa.select(StageModel).order_by(StageModel.created_at)
        )
        return [_stage_from(m) for m in result.scalars()]

    async def list_for_user(self, user_id: UUID) -> list[UserStage]:
        result = await self._session.execute(
            sa.select(UserStageModel).where(UserStageModel.user_id == user_id)
        )
        return [_user_stage_from(m) for m in result.scalars()]

    async def attach_to_user(self, user_id: UUID, stage_id: UUID) -> UserStage:
        existing = await self._session.execute(
            sa.select(UserStageModel).where(
                UserStageModel.user_id == user_id,
                UserStageModel.stage_id == stage_id,
            )
        )
        if existing.scalar_one_or_none() is not None:
            raise StageAlreadyAttached(f"Stage {stage_id} already attached to user {user_id}.")
        now = now_sp()
        model = UserStageModel(user_id=user_id, stage_id=stage_id, done=False, updated_at=now)
        self._session.add(model)
        await self._session.flush()
        return _user_stage_from(model)

    async def detach_from_user(self, user_id: UUID, stage_id: UUID) -> None:
        await self._session.execute(
            sa.delete(UserStageModel).where(
                UserStageModel.user_id == user_id,
                UserStageModel.stage_id == stage_id,
            )
        )

    async def set_done(self, user_id: UUID, stage_id: UUID, done: bool) -> UserStage:
        now = now_sp()
        result = await self._session.execute(
            sa.update(UserStageModel)
            .where(
                UserStageModel.user_id == user_id,
                UserStageModel.stage_id == stage_id,
            )
            .values(done=done, updated_at=now)
            .returning(UserStageModel)
        )
        m = result.scalar_one_or_none()
        if m is None:
            raise StageNotFound(f"UserStage not found for user {user_id}, stage {stage_id}.")
        return _user_stage_from(m)
