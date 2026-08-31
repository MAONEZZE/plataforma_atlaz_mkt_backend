from dataclasses import dataclass
from uuid import UUID

from app.domain.event_module.event_exceptions import EventNotFound
from app.domain.event_module.event_repo_interface import EventRepository
from app.domain.user_module.user_exceptions import InvalidPhoto
from app.services.event_module.event_image_storage_gateway import EventImageStorageGateway
from app.services.user_module.image_validation import detect_image_mime

_EXTENSION_MAP: dict[str, str] = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}

_MAX_SIZE = 5 * 1024 * 1024  # 5 MB


@dataclass(frozen=True)
class UploadEventImageInput:
    event_id: UUID
    content_type: str
    data: bytes


@dataclass(frozen=True)
class EventImageUrlDTO:
    image_url: str


class UploadEventImage:
    def __init__(self, repo: EventRepository, storage: EventImageStorageGateway) -> None:
        self._repo = repo
        self._storage = storage

    async def execute(self, inp: UploadEventImageInput) -> EventImageUrlDTO:
        if inp.content_type not in _EXTENSION_MAP:
            raise InvalidPhoto("Tipo de imagem não suportado. Use JPEG, PNG ou WebP.")

        if len(inp.data) > _MAX_SIZE:
            raise InvalidPhoto("Imagem deve ter no máximo 5 MB.")

        detected = detect_image_mime(inp.data)
        if detected != inp.content_type:
            raise InvalidPhoto("Conteúdo do arquivo não corresponde ao tipo declarado.")

        event = await self._repo.get_by_id(inp.event_id)
        if event is None:
            raise EventNotFound(f"Event {inp.event_id} not found.")

        ext = _EXTENSION_MAP[inp.content_type]
        image_url = await self._storage.upload(
            event_id=inp.event_id,
            data=inp.data,
            content_type=inp.content_type,
            extension=ext,
        )

        event.image_url = image_url
        await self._repo.update(event)

        return EventImageUrlDTO(image_url=image_url)
