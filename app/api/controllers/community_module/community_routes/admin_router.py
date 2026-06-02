from uuid import uuid4

from fastapi import APIRouter, Depends, File, UploadFile
from pydantic import BaseModel

from app.api.config.dependencies.auth_deps import require_admin
from app.api.config.settings import settings
from app.database.shared.supabase_client import create_supabase_admin_client
from app.domain.shared.base_exceptions import AppException
from app.services.user_module.image_validation import detect_image_mime

admin_router = APIRouter(prefix="/admin", tags=["admin-community"])


class CoverUrlOut(BaseModel):
    cover_url: str


_COVER_EXT_MAP: dict[str, str] = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}
_COVER_MAX_SIZE = 5 * 1024 * 1024


@admin_router.post("/community/photo", response_model=CoverUrlOut)
async def upload_community_photo(
    image: UploadFile = File(...),
    _=Depends(require_admin),
) -> CoverUrlOut:
    content_type = image.content_type or ""
    if content_type not in _COVER_EXT_MAP:
        raise AppException(
            "VALIDATION_ERROR", "Tipo de imagem não suportado. Use JPEG, PNG ou WebP.", 400
        )

    data = await image.read()
    if len(data) > _COVER_MAX_SIZE:
        raise AppException("VALIDATION_ERROR", "Imagem deve ter no máximo 5 MB.", 400)

    detected = detect_image_mime(data)
    if detected != content_type:
        raise AppException(
            "VALIDATION_ERROR", "Conteúdo do arquivo não corresponde ao tipo declarado.", 400
        )

    ext = _COVER_EXT_MAP[content_type]
    path = f"pictures/communities/{uuid4()}.{ext}"
    client = create_supabase_admin_client()
    client.storage.from_(settings.SUPABASE_BUCKET).upload(
        path,
        data,
        file_options={"content-type": content_type, "upsert": "true"},
    )
    cover_url = client.storage.from_(settings.SUPABASE_BUCKET).get_public_url(path)
    return CoverUrlOut(cover_url=cover_url)
