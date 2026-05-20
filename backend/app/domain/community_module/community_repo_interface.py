from typing import Protocol

from app.domain.community_module.community_model import CommunityMember


class CommunityRepository(Protocol):
    async def list_active(
        self, page: int, page_size: int
    ) -> tuple[list[CommunityMember], int]: ...
