from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.contexts.auth.domain.entities import User as AuthUser
from app.contexts.users.application.dtos import UpdateMeInput, UploadPhotoInput
from app.contexts.users.application.use_cases.update_me import UpdateMe
from app.contexts.users.application.use_cases.get_me import GetMe
from app.contexts.users.application.use_cases.upload_photo import UploadPhoto
from app.contexts.users.domain.exceptions import InvalidPhoto, UserNotFound
from app.contexts.users.infrastructure.repositories import SqlAlchemyUserRepository
from app.contexts.users.infrastructure.supabase_storage_gateway import SupabaseStorageGateway
from app.contexts.users.presentation.schemas import (
    PhotoUrlResponse,
    PatchMeBody,
    UserResponse,
)
from app.core.db import get_session
from app.core.deps import get_current_user
from app.core.exceptions import AppException
from app.shared.domain.exceptions import DomainError
from app.shared.infrastructure.supabase_client import create_supabase_admin_client

router = APIRouter(prefix="/me", tags=["me"])


def _get_me(session: AsyncSession = Depends(get_session)) -> GetMe:
    return GetMe(repo=SqlAlchemyUserRepository(session))


def _update_me(session: AsyncSession = Depends(get_session)) -> UpdateMe:
    return UpdateMe(repo=SqlAlchemyUserRepository(session))


def _upload_photo(session: AsyncSession = Depends(get_session)) -> UploadPhoto:
    client = create_supabase_admin_client()
    return UploadPhoto(
        repo=SqlAlchemyUserRepository(session),
        storage=SupabaseStorageGateway(client),
    )


@router.get("", response_model=UserResponse)
async def get_me(
    current_user: AuthUser = Depends(get_current_user),
    use_case: GetMe = Depends(_get_me),
) -> UserResponse:
    try:
        user = await use_case.execute(current_user.id)
    except UserNotFound as exc:
        raise AppException("RESOURCE_NOT_FOUND", "Usuário não encontrado.", 404) from exc
    return UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        phone=user.phone,
        linkedin_url=user.linkedin_url,
        instagram_username=user.instagram_username,
        description=user.description,
        photo_url=user.photo_url,
        role=user.role,
        created_at=user.created_at,
    )


@router.patch("", response_model=UserResponse)
async def patch_me(
    body: PatchMeBody,
    current_user: AuthUser = Depends(get_current_user),
    use_case: UpdateMe = Depends(_update_me),
) -> UserResponse:
    inp = UpdateMeInput(
        name=body.name,
        phone=body.phone,
        linkedin_url=body.linkedin_url,
        instagram_username=body.instagram_username,
        description=body.description,
    )
    try:
        user = await use_case.execute(current_user.id, inp)
    except UserNotFound as exc:
        raise AppException("RESOURCE_NOT_FOUND", "Usuário não encontrado.", 404) from exc
    except DomainError as exc:
        raise AppException("VALIDATION_ERROR", str(exc), 400) from exc
    return UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        phone=user.phone,
        linkedin_url=user.linkedin_url,
        instagram_username=user.instagram_username,
        description=user.description,
        photo_url=user.photo_url,
        role=user.role,
        created_at=user.created_at,
    )


@router.post("/photo", response_model=PhotoUrlResponse)
async def post_photo(
    photo: UploadFile = File(...),
    current_user: AuthUser = Depends(get_current_user),
    use_case: UploadPhoto = Depends(_upload_photo),
) -> PhotoUrlResponse:
    data = await photo.read()
    inp = UploadPhotoInput(
        user_id=current_user.id,
        content_type=photo.content_type or "",
        data=data,
    )
    try:
        result = await use_case.execute(inp)
    except InvalidPhoto as exc:
        raise AppException("VALIDATION_ERROR", str(exc), 400) from exc
    except UserNotFound as exc:
        raise AppException("RESOURCE_NOT_FOUND", "Usuário não encontrado.", 404) from exc
    return PhotoUrlResponse(photo_url=result.photo_url)
