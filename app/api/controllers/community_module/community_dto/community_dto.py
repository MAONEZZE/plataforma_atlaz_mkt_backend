# Merged from: contexts/community/application/dtos.py + contexts/community/presentation/schemas.py
from dataclasses import dataclass
from uuid import UUID

from pydantic import BaseModel, ConfigDict

# ── Application DTOs ───────────────────────────────────────────────────────────

@dataclass(frozen=True)
class CommunityMemberDTO:
    id: UUID
    name: str
    photo_url: str | None
    linkedin_url: str | None
    instagram_username: str | None


@dataclass(frozen=True)
class ListCommunityResultDTO:
    items: list[CommunityMemberDTO]
    page: int
    page_size: int
    total: int


# ── Presentation Schemas ───────────────────────────────────────────────────────

class CommunityMemberSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    photo_url: str | None
    linkedin_url: str | None
    instagram_username: str | None


class ListCommunityResponse(BaseModel):
    items: list[CommunityMemberSchema]
    page: int
    page_size: int
    total: int
