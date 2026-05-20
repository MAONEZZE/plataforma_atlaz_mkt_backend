from app.contexts.users.application.dtos import PhotoUrlDTO, UploadPhotoInput
from app.contexts.users.application.storage_gateway import PhotoStorageGateway
from app.contexts.users.domain.exceptions import InvalidPhoto, UserNotFound
from app.contexts.users.domain.repositories import UserRepository
from app.contexts.users.infrastructure.image_validation import detect_image_mime

_EXTENSION_MAP: dict[str, str] = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}

_MAX_SIZE = 5 * 1024 * 1024  # 5 MB


class UploadPhoto:
    def __init__(self, repo: UserRepository, storage: PhotoStorageGateway) -> None:
        self._repo = repo
        self._storage = storage

    async def execute(self, inp: UploadPhotoInput) -> PhotoUrlDTO:
        if inp.content_type not in _EXTENSION_MAP:
            raise InvalidPhoto("Tipo de imagem não suportado. Use JPEG, PNG ou WebP.")

        if len(inp.data) > _MAX_SIZE:
            raise InvalidPhoto("Imagem deve ter no máximo 5 MB.")

        detected = detect_image_mime(inp.data)
        if detected != inp.content_type:
            raise InvalidPhoto("Conteúdo do arquivo não corresponde ao tipo declarado.")

        user = await self._repo.get_by_id(inp.usuario_id)
        if user is None:
            raise UserNotFound("Usuário não encontrado.")

        ext = _EXTENSION_MAP[inp.content_type]
        foto_url = self._storage.upload(
            usuario_id=inp.usuario_id,
            data=inp.data,
            content_type=inp.content_type,
            extension=ext,
        )

        user.foto_url = foto_url
        await self._repo.update(user)

        return PhotoUrlDTO(foto_url=foto_url)
