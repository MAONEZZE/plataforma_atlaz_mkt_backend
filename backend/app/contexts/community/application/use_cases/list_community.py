from app.contexts.community.application.dtos import ListCommunityResultDTO, CommunityMemberDTO
from app.contexts.community.domain.repositories import CommunityRepository


class ListCommunity:
    def __init__(self, repo: CommunityRepository) -> None:
        self._repo = repo

    async def execute(self, page: int, page_size: int) -> ListCommunityResultDTO:
        members, total = await self._repo.list_active(page=page, page_size=page_size)
        return ListCommunityResultDTO(
            items=[
                CommunityMemberDTO(
                    id=m.id,
                    name=m.name,
                    photo_url=m.photo_url,
                    linkedin_url=m.linkedin_url,
                    instagram_username=m.instagram_username,
                )
                for m in members
            ],
            page=page,
            page_size=page_size,
            total=total,
        )
