from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


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
