from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class StageIn(BaseModel):
    text: str


class StageOut(BaseModel):
    id: UUID
    text: str
    created_at: datetime


class UserStageOut(BaseModel):
    user_id: UUID
    stage_id: UUID
    done: bool
    updated_at: datetime


class SetDoneIn(BaseModel):
    done: bool
