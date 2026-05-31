from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class Stage:
    id: UUID
    text: str
    created_at: datetime
    title: str | None = None


@dataclass
class UserStage:
    user_id: UUID
    stage_id: UUID
    done: bool
    updated_at: datetime
