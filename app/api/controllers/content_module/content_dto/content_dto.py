from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ── Application DTOs ───────────────────────────────────────────────────────────

@dataclass
class TrackProgressDTO:
    id: UUID
    title: str
    description: str | None
    cover_url: str | None
    total_lessons: int
    lessons_completed: int
    progress_pct: float


@dataclass
class LessonSummaryDTO:
    id: UUID
    title: str
    duration_minutes: int | None
    order: int
    completed: bool
    is_doc: bool


@dataclass
class ModuleWithLessonsDTO:
    id: UUID
    title: str
    description: str | None
    order: int
    lessons: list[LessonSummaryDTO]


@dataclass
class TrackWithModulesDTO:
    id: UUID
    title: str
    description: str | None
    cover_url: str | None
    progress_pct: float
    modules: list[ModuleWithLessonsDTO]


@dataclass
class TrackSummaryDTO:
    id: UUID
    title: str


@dataclass
class LessonDetailDTO:
    id: UUID
    module_id: UUID
    title: str
    description: str | None
    drive_file_id: str
    duration_minutes: int | None
    completed: bool
    is_doc: bool
    track: TrackSummaryDTO
    next_lesson: LessonSummaryDTO | None


@dataclass
class AuthorDTO:
    id: UUID
    name: str
    photo_url: str | None


@dataclass
class CommentDTO:
    id: UUID
    author: AuthorDTO
    text: str | None
    created_at: datetime
    edited_at: datetime | None
    deleted_at: datetime | None
    is_own: bool


# ── Presentation Schemas ───────────────────────────────────────────────────────

class TrackProgressOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str | None
    cover_url: str | None
    total_lessons: int
    lessons_completed: int
    progress_pct: float


class LessonSummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    duration_minutes: int | None
    order: int
    completed: bool
    is_doc: bool


class ModuleWithLessonsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str | None
    order: int
    lessons: list[LessonSummaryOut]


class TrackSummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str


class TrackWithModulesOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str | None
    cover_url: str | None
    progress_pct: float
    modules: list[ModuleWithLessonsOut]


class LessonDetailOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    module_id: UUID
    title: str
    description: str | None
    drive_file_id: str
    duration_minutes: int | None
    completed: bool
    is_doc: bool
    track: TrackSummaryOut
    next_lesson: LessonSummaryOut | None


class CreateTrackIn(BaseModel):
    title: str
    description: str | None = None
    cover_url: str | None = None
    order: int = 0


class UpdateTrackIn(BaseModel):
    title: str | None = None
    description: str | None = None
    cover_url: str | None = None
    order: int | None = None


class OrderItem(BaseModel):
    id: UUID
    order: int


class ReorderIn(BaseModel):
    order: list[OrderItem]


class CreateModuleIn(BaseModel):
    track_id: UUID
    title: str
    description: str | None = None
    order: int = 0


class UpdateModuleIn(BaseModel):
    title: str | None = None
    description: str | None = None
    order: int | None = None


class CreateLessonIn(BaseModel):
    module_id: UUID
    title: str
    description: str | None = None
    drive_url: str | None = None
    document_url: str | None = None
    duration_minutes: int | None = None
    order: int = 0
    is_doc: bool = False


class UpdateLessonIn(BaseModel):
    title: str | None = None
    description: str | None = None
    drive_url: str | None = None
    document_url: str | None = None
    duration_minutes: int | None = None
    order: int | None = None
    is_doc: bool | None = None


class TrackAdminOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str | None
    cover_url: str | None
    order: int
    created_at: datetime


class ModuleAdminOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    track_id: UUID
    title: str
    description: str | None
    order: int


class LessonAdminOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    module_id: UUID
    title: str
    description: str | None
    drive_file_id: str
    duration_minutes: int | None
    order: int
    is_doc: bool
    created_at: datetime


class AuthorOut(BaseModel):
    id: UUID
    name: str
    photo_url: str | None


class CommentOut(BaseModel):
    id: UUID
    author: AuthorOut
    text: str | None
    created_at: datetime
    edited_at: datetime | None
    deleted_at: datetime | None
    is_own: bool


class CreateCommentIn(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)


class EditCommentIn(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)
