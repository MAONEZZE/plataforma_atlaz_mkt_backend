from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CommunityMemberSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    nome: str
    foto_url: str | None
    linkedin_url: str | None
    instagram_username: str | None


class ListCommunityResponse(BaseModel):
    items: list[CommunityMemberSchema]
    page: int
    page_size: int
    total: int
