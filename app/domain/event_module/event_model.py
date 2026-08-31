from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID


@dataclass
class EventDate:
    id: UUID
    client_id: UUID | None
    title: str
    date: date
    description: str | None
    image_url: str | None
    created_at: datetime
    updated_at: datetime
