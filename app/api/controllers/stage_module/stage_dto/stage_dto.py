from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class StageIn(BaseModel):
    text: str
    title: str | None = None
    folder_id: UUID | None = None
    order: int = 0


class StageOut(BaseModel):
    id: UUID
    text: str
    title: str | None
    folder_id: UUID | None = None
    order: int = 0
    created_at: datetime


class UserStageOut(BaseModel):
    user_id: UUID
    stage_id: UUID
    done: bool
    updated_at: datetime
    title: str | None = None
    text: str | None = None
    folder_id: UUID | None = None
    folder_title: str | None = None
    order: int = 0


class SetDoneIn(BaseModel):
    done: bool


class FolderIn(BaseModel):
    title: str
    order: int = 0


class FolderPatchIn(BaseModel):
    title: str | None = None
    order: int | None = None


class FolderOut(BaseModel):
    id: UUID
    title: str
    order: int
    created_at: datetime
