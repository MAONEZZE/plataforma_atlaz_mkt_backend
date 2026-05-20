from app.contexts.community.application.dtos import ListCommunityResultDTO, CommunityMemberDTO
from app.contexts.community.domain.repositories import CommunityRepository


class ListCommunity:
    def __init__(self, repo: CommunityRepository) -> None:
        self._repo = repo

    async def execute(self, page: int, page_size: int) -> ListCommunityResultDTO:
        membros, total = await self._repo.list_active(page=page, page_size=page_size)
        return ListCommunityResultDTO(
            items=[
                CommunityMemberDTO(
                    id=m.id,
                    nome=m.nome,
                    foto_url=m.foto_url,
                    linkedin_url=m.linkedin_url,
                    instagram_username=m.instagram_username,
                )
                for m in membros
            ],
            page=page,
            page_size=page_size,
            total=total,
        )
