from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PatchMeBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    phone: str | None = None
    linkedin_url: str | None = None
    instagram_username: str | None = None
    description: str | None = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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


class PhotoUrlResponse(BaseModel):
    photo_url: str
