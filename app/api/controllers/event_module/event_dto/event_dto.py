from datetime import date as _date
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class EventIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    date: _date
    description: str | None = None
    client_id: UUID | None = None


class EventPatchIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = None
    date: _date | None = None
    description: str | None = None
    client_id: UUID | None = None


class EventOut(BaseModel):
    id: UUID
    client_id: UUID | None
    title: str
    date: _date
    description: str | None
    image_url: str | None
    created_at: datetime
    updated_at: datetime


class ClientEventOut(BaseModel):
    id: UUID
    title: str
    date: _date
    description: str | None
    image_url: str | None
    is_global: bool


class ListEventsResponse(BaseModel):
    items: list[EventOut]
    page: int
    page_size: int
    total: int


class ListClientEventsResponse(BaseModel):
    items: list[ClientEventOut]
    page: int
    page_size: int
    total: int


class EventImageUrlOut(BaseModel):
    image_url: str


class DeletedEventsCountOut(BaseModel):
    deleted: int
