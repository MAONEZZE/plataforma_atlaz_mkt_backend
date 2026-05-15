from typing import Protocol
from uuid import UUID


class FotoStorageGateway(Protocol):
    def upload(
        self,
        usuario_id: UUID,
        data: bytes,
        content_type: str,
        extension: str,
    ) -> str: ...
