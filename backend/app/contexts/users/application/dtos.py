from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class UserDTO:
    id: UUID
    name: str
    email: str
    phone: str | None
    linkedin_url: str | None
    instagram_username: str | None
    description: str | None
    photo_url: str | None
    role: str
    created_at: datetime


@dataclass(frozen=True)
class UpdateMeInput:
    name: str | None
    phone: str | None
    linkedin_url: str | None
    instagram_username: str | None
    description: str | None = None


@dataclass(frozen=True)
class UploadPhotoInput:
    user_id: UUID
    content_type: str
    data: bytes


@dataclass(frozen=True)
class PhotoUrlDTO:
    photo_url: str
