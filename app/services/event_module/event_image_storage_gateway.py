from typing import Protocol
from uuid import UUID


class EventImageStorageGateway(Protocol):
    async def upload(
        self,
        event_id: UUID,
        data: bytes,
        content_type: str,
        extension: str,
    ) -> str: ...
