from app.api.controllers.user_module.user_dto.user_dto import PhotoUrlDTO, UploadPhotoInput
from app.domain.user_module.user_exceptions import InvalidPhoto, UserNotFound
from app.domain.user_module.user_repo_interface import UserRepository
from app.services.user_module.image_validation import detect_image_mime
from app.services.user_module.storage_gateway import PhotoStorageGateway

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

        user = await self._repo.get_by_id(inp.user_id)
        if user is None:
            raise UserNotFound("Usuário não encontrado.")

        ext = _EXTENSION_MAP[inp.content_type]
        photo_url = await self._storage.upload(
            user_id=inp.user_id,
            data=inp.data,
            content_type=inp.content_type,
            extension=ext,
        )

        user.photo_url = photo_url
        await self._repo.update(user)

        return PhotoUrlDTO(photo_url=photo_url)
