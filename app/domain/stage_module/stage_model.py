from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class StageFolder:
    id: UUID
    title: str
    order: int
    created_at: datetime


@dataclass
class Stage:
    id: UUID
    text: str
    created_at: datetime
    title: str | None = None
    folder_id: UUID | None = None
    order: int = 0


@dataclass
class UserStage:
    user_id: UUID
    stage_id: UUID
    done: bool
    updated_at: datetime
