from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class Track:
    id: UUID
    title: str
    description: str | None
    cover_url: str | None
    order: int
    created_at: datetime


@dataclass
class Module:
    id: UUID
    track_id: UUID
    title: str
    description: str | None
    order: int


@dataclass
class Lesson:
    id: UUID
    module_id: UUID
    title: str
    description: str | None
    drive_file_id: str
    duration_minutes: int | None
    order: int
    is_doc: bool
    created_at: datetime


@dataclass
class Comment:
    id: UUID
    lesson_id: UUID
    user_id: UUID
    text: str
    created_at: datetime
    edited_at: datetime | None
    deleted_at: datetime | None


@dataclass
class CommentRead:
    """Comment with denormalized author data for listing."""

    id: UUID
    lesson_id: UUID
    user_id: UUID
    text: str | None
    created_at: datetime
    edited_at: datetime | None
    deleted_at: datetime | None
    author_name: str
    author_photo_url: str | None
