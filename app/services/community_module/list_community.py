from app.api.controllers.community_module.community_dto.community_dto import (
    CommunityMemberDTO,
    ListCommunityResultDTO,
)
from app.domain.community_module.community_repo_interface import CommunityRepository


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
                    description=m.description,
                    product_name=m.product_name,
                )
                for m in members
            ],
            page=page,
            page_size=page_size,
            total=total,
        )
