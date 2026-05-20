from typing import Protocol

from app.contexts.community.domain.entities import CommunityMember


class CommunityRepository(Protocol):
    async def list_active(
        self, page: int, page_size: int
    ) -> tuple[list[CommunityMember], int]: ...
