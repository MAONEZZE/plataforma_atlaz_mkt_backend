from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.contexts.auth.domain.entities import User as AuthUser
from app.contexts.users.application.dtos import UpdateMeInput, UploadPhotoInput
from app.contexts.users.application.use_cases.update_me import UpdateMe
from app.contexts.users.application.use_cases.get_me import ObterMe
from app.contexts.users.application.use_cases.upload_photo import UploadPhoto
from app.contexts.users.domain.exceptions import InvalidPhoto, UserNotFound
from app.contexts.users.infrastructure.repositories import SqlAlchemyUserRepository
from app.contexts.users.infrastructure.supabase_storage_gateway import SupabaseStorageGateway
from app.contexts.users.presentation.schemas import (
    PhotoUrlResponse,
    PatchMeBody,
    UsuarioResponse,
)
from app.core.db import get_session
from app.core.deps import get_current_user
from app.core.exceptions import AppException
from app.shared.domain.exceptions import DomainError
from app.shared.infrastructure.supabase_client import create_supabase_admin_client

router = APIRouter(prefix="/me", tags=["me"])


def _obter_me(session: AsyncSession = Depends(get_session)) -> ObterMe:
    return ObterMe(repo=SqlAlchemyUserRepository(session))


def _update_me(session: AsyncSession = Depends(get_session)) -> UpdateMe:
    return UpdateMe(repo=SqlAlchemyUserRepository(session))


def _upload_photo(session: AsyncSession = Depends(get_session)) -> UploadPhoto:
    client = create_supabase_admin_client()
    return UploadPhoto(
        repo=SqlAlchemyUserRepository(session),
        storage=SupabaseStorageGateway(client),
    )


@router.get("", response_model=UsuarioResponse)
async def get_me(
    current_user: AuthUser = Depends(get_current_user),
    use_case: ObterMe = Depends(_obter_me),
) -> UsuarioResponse:
    try:
        usuario = await use_case.execute(current_user.id)
    except UserNotFound as exc:
        raise AppException("RESOURCE_NOT_FOUND", "Usuário não encontrado.", 404) from exc
    return UsuarioResponse(
        id=usuario.id,
        nome=usuario.nome,
        email=usuario.email,
        telefone=usuario.telefone,
        linkedin_url=usuario.linkedin_url,
        instagram_username=usuario.instagram_username,
        descricao=usuario.descricao,
        foto_url=usuario.foto_url,
        role=usuario.role,
        criado_em=usuario.criado_em,
    )


@router.patch("", response_model=UsuarioResponse)
async def patch_me(
    body: PatchMeBody,
    current_user: AuthUser = Depends(get_current_user),
    use_case: UpdateMe = Depends(_update_me),
) -> UsuarioResponse:
    inp = UpdateMeInput(
        nome=body.nome,
        telefone=body.telefone,
        linkedin_url=body.linkedin_url,
        instagram_username=body.instagram_username,
        descricao=body.descricao,
    )
    try:
        usuario = await use_case.execute(current_user.id, inp)
    except UserNotFound as exc:
        raise AppException("RESOURCE_NOT_FOUND", "Usuário não encontrado.", 404) from exc
    except DomainError as exc:
        raise AppException("VALIDATION_ERROR", str(exc), 400) from exc
    return UsuarioResponse(
        id=usuario.id,
        nome=usuario.nome,
        email=usuario.email,
        telefone=usuario.telefone,
        linkedin_url=usuario.linkedin_url,
        instagram_username=usuario.instagram_username,
        descricao=usuario.descricao,
        foto_url=usuario.foto_url,
        role=usuario.role,
        criado_em=usuario.criado_em,
    )


@router.post("/foto", response_model=PhotoUrlResponse)
async def post_foto(
    foto: UploadFile = File(...),
    current_user: AuthUser = Depends(get_current_user),
    use_case: UploadPhoto = Depends(_upload_photo),
) -> PhotoUrlResponse:
    data = await foto.read()
    inp = UploadPhotoInput(
        usuario_id=current_user.id,
        content_type=foto.content_type or "",
        data=data,
    )
    try:
        result = await use_case.execute(inp)
    except InvalidPhoto as exc:
        raise AppException("VALIDATION_ERROR", str(exc), 400) from exc
    except UserNotFound as exc:
        raise AppException("RESOURCE_NOT_FOUND", "Usuário não encontrado.", 404) from exc
    return PhotoUrlResponse(foto_url=result.foto_url)
