from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


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


# ── Presentation Schemas ───────────────────────────────────────────────────────

class PatchMeBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    phone: str | None = None
    linkedin_url: str | None = None
    instagram_username: str | None = None
    description: str | None = None


class CreateClientBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    email: EmailStr
    password: str
    phone: str | None = None
    product_id: UUID | None = None


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
    product_id: UUID | None = None
    product_name: str | None = None
    created_at: datetime


class PhotoUrlResponse(BaseModel):
    photo_url: str


class ClientSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    email: str
    phone: str | None
    product_id: UUID | None = None
    product_name: str | None = None


class ListClientsResponse(BaseModel):
    items: list[ClientSummaryResponse]
    page: int
    page_size: int
    total: int
