from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class CommunityMemberDTO:
    id: UUID
    nome: str
    foto_url: str | None
    linkedin_url: str | None
    instagram_username: str | None


@dataclass(frozen=True)
class ListCommunityResultDTO:
    items: list[CommunityMemberDTO]
    page: int
    page_size: int
    total: int
