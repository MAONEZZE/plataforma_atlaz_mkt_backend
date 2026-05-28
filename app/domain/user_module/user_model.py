from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class User:
    id: UUID
    name: str
    email: str
    phone: str | None
    linkedin_url: str | None
    instagram_username: str | None
    description: str | None
    photo_url: str | None
    role: str
    inactive: bool
    created_at: datetime
    updated_at: datetime
    product_id: UUID | None = None
