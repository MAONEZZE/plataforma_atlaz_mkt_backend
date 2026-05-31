from dataclasses import dataclass
from uuid import UUID


@dataclass
class CommunityMember:
    id: UUID
    name: str
    photo_url: str | None
    linkedin_url: str | None
    instagram_username: str | None
    description: str | None
    product_name: str | None
