from app.contexts.usuarios.application.dtos import FotoUrlDTO, UploadFotoInput
from app.contexts.usuarios.application.storage_gateway import FotoStorageGateway
from app.contexts.usuarios.domain.exceptions import FotoInvalida, UsuarioNaoEncontrado
from app.contexts.usuarios.domain.repositories import UsuarioRepository
from app.contexts.usuarios.infrastructure.image_validation import detect_image_mime

_EXTENSION_MAP: dict[str, str] = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}

_MAX_SIZE = 5 * 1024 * 1024  # 5 MB


class UploadFoto:
    def __init__(self, repo: UsuarioRepository, storage: FotoStorageGateway) -> None:
        self._repo = repo
        self._storage = storage

    async def execute(self, inp: UploadFotoInput) -> FotoUrlDTO:
        if inp.content_type not in _EXTENSION_MAP:
            raise FotoInvalida("Tipo de imagem não suportado. Use JPEG, PNG ou WebP.")

        if len(inp.data) > _MAX_SIZE:
            raise FotoInvalida("Imagem deve ter no máximo 5 MB.")

        detected = detect_image_mime(inp.data)
        if detected != inp.content_type:
            raise FotoInvalida("Conteúdo do arquivo não corresponde ao tipo declarado.")

        user = await self._repo.por_id(inp.usuario_id)
        if user is None:
            raise UsuarioNaoEncontrado("Usuário não encontrado.")

        ext = _EXTENSION_MAP[inp.content_type]
        foto_url = self._storage.upload(
            usuario_id=inp.usuario_id,
            data=inp.data,
            content_type=inp.content_type,
            extension=ext,
        )

        user.foto_url = foto_url
        await self._repo.atualizar(user)

        return FotoUrlDTO(foto_url=foto_url)
