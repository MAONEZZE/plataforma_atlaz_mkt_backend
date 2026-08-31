from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.config.dependencies.auth_deps import require_admin
from app.api.controllers.user_module.user_dto.user_dto import (
    AdminClientCreatedResponse,
    AdminClientDetailResponse,
    AdminClientUpdatedResponse,
    ClientEventResponse,
    ClientStageResponse,
    ClientSummaryResponse,
    CreateClientBody,
    ListClientsResponse,
    PhotoUrlResponse,
    UpdateClientBody,
    UploadPhotoInput,
)
from app.database.event_module.event_repo import SqlAlchemyEventRepository
from app.database.product_module.product_repo import SqlAlchemyProductRepository
from app.database.shared.db_factory import get_session
from app.database.shared.supabase_client import create_supabase_admin_client
from app.database.stage_module.stage_repo import SqlAlchemyStageRepository
from app.database.user_module.user_repo import SqlAlchemyUserRepository
from app.domain.auth_module.auth_model import User as AuthUser
from app.domain.product_module.product_exceptions import ProductNotFound
from app.domain.shared.base_exceptions import AppException, DomainError
from app.domain.user_module.user_exceptions import (
    EmailAlreadyRegistered,
    InvalidPhoto,
    SupabaseAdminError,
    UserNotFound,
    UserTriggerSyncFailed,
)
from app.services.user_module.create_client_service import (
    CreateClient,
    CreateClientInput,
)
from app.services.user_module.delete_client_service import DeleteClient, DeleteClientInput
from app.services.user_module.get_client_service import GetClient
from app.services.user_module.list_clients_service import (
    ListClients,
    ListClientsInput,
)
from app.services.user_module.supabase_admin_gateway import (
    SupabaseAdminUserGatewayImpl,
)
from app.services.user_module.supabase_storage_gateway import SupabaseStorageGateway
from app.services.user_module.update_client_service import UpdateClient, UpdateClientInput
from app.services.user_module.upload_photo_service import UploadPhoto

admin_router = APIRouter(prefix="/admin", tags=["admin-clients"])


def _create_client(session: AsyncSession = Depends(get_session)) -> CreateClient:
    gateway = SupabaseAdminUserGatewayImpl(create_supabase_admin_client())
    return CreateClient(
        repo=SqlAlchemyUserRepository(session),
        gateway=gateway,
        product_repo=SqlAlchemyProductRepository(session),
        stage_repo=SqlAlchemyStageRepository(session),
    )


def _list_clients(session: AsyncSession = Depends(get_session)) -> ListClients:
    return ListClients(repo=SqlAlchemyUserRepository(session))


def _update_client(session: AsyncSession = Depends(get_session)) -> UpdateClient:
    return UpdateClient(
        repo=SqlAlchemyUserRepository(session),
        product_repo=SqlAlchemyProductRepository(session),
        stage_repo=SqlAlchemyStageRepository(session),
    )


def _delete_client(session: AsyncSession = Depends(get_session)) -> DeleteClient:
    gateway = SupabaseAdminUserGatewayImpl(create_supabase_admin_client())
    return DeleteClient(repo=SqlAlchemyUserRepository(session), gateway=gateway)


def _stage_repo(session: AsyncSession = Depends(get_session)) -> SqlAlchemyStageRepository:
    return SqlAlchemyStageRepository(session)


def _get_client(session: AsyncSession = Depends(get_session)) -> GetClient:
    return GetClient(repo=SqlAlchemyUserRepository(session))


def _event_repo(session: AsyncSession = Depends(get_session)) -> SqlAlchemyEventRepository:
    return SqlAlchemyEventRepository(session)


def _upload_client_photo(session: AsyncSession = Depends(get_session)) -> UploadPhoto:
    client = create_supabase_admin_client()
    return UploadPhoto(
        repo=SqlAlchemyUserRepository(session),
        storage=SupabaseStorageGateway(client),
    )


@admin_router.post(
    "/clients",
    response_model=AdminClientCreatedResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_client(
    body: CreateClientBody,
    _admin: AuthUser = Depends(require_admin),
    use_case: CreateClient = Depends(_create_client),
) -> AdminClientCreatedResponse:
    inp = CreateClientInput(
        name=body.name,
        email=body.email,
        password=body.password,
        phone=body.phone,
        description=body.description,
        product_id=body.product_id,
        stage_ids=tuple(body.stage_ids),
    )
    try:
        user = await use_case.execute(inp)
    except EmailAlreadyRegistered as exc:
        raise AppException("EMAIL_ALREADY_REGISTERED", str(exc), 409) from exc
    except UserTriggerSyncFailed as exc:
        raise AppException("INTERNAL_ERROR", str(exc), 500) from exc
    except SupabaseAdminError as exc:
        raise AppException("INTERNAL_ERROR", str(exc), 502) from exc
    except ProductNotFound as exc:
        raise AppException("PRODUCT_NOT_FOUND", str(exc), 404) from exc
    except DomainError as exc:
        raise AppException("VALIDATION_ERROR", str(exc), 400) from exc

    return AdminClientCreatedResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        product_id=user.product_id,
        product_name=user.product_name,
        photo_url=user.photo_url,
    )


@admin_router.get("/clients", response_model=ListClientsResponse)
async def list_clients(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    busca: str | None = Query(default=None),
    ordenar: Literal["name", "created_at"] | None = Query(default=None),
    direcao: Literal["asc", "desc"] = Query(default="asc"),
    _admin: AuthUser = Depends(require_admin),
    use_case: ListClients = Depends(_list_clients),
    stage_repo: SqlAlchemyStageRepository = Depends(_stage_repo),
) -> ListClientsResponse:
    items, total = await use_case.execute(
        ListClientsInput(
            page=page, page_size=page_size, search=busca, sort=ordenar, order=direcao
        )
    )
    user_ids = [u.id for u in items]
    stage_rows = await stage_repo.list_for_users(user_ids) if user_ids else []
    stages_by_user: dict = {}
    for user_id, stage, done in stage_rows:
        stages_by_user.setdefault(user_id, []).append(
            ClientStageResponse(stage_id=stage.id, title=stage.title, text=stage.text, done=done)
        )
    return ListClientsResponse(
        items=[
            ClientSummaryResponse(
                id=u.id,
                name=u.name,
                email=u.email,
                phone=u.phone,
                description=u.description,
                product_id=u.product_id,
                product_name=u.product_name,
                stages=stages_by_user.get(u.id, []),
            )
            for u in items
        ],
        page=page,
        page_size=page_size,
        total=total,
    )


@admin_router.get("/clients/{client_id}", response_model=AdminClientDetailResponse)
async def get_client(
    client_id: UUID,
    _admin: AuthUser = Depends(require_admin),
    use_case: GetClient = Depends(_get_client),
    stage_repo: SqlAlchemyStageRepository = Depends(_stage_repo),
    event_repo: SqlAlchemyEventRepository = Depends(_event_repo),
) -> AdminClientDetailResponse:
    try:
        user = await use_case.execute(client_id)
    except UserNotFound as exc:
        raise AppException("CLIENT_NOT_FOUND", str(exc), 404) from exc

    stage_rows = await stage_repo.list_for_user(user.id)
    stages = [
        ClientStageResponse(stage_id=stage.id, title=stage.title, text=stage.text, done=us.done)
        for us, stage in stage_rows
    ]
    events = await event_repo.list_for_client_only(user.id)
    return AdminClientDetailResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        phone=user.phone,
        linkedin_url=user.linkedin_url,
        instagram_username=user.instagram_username,
        description=user.description,
        photo_url=user.photo_url,
        role=user.role,
        product_id=user.product_id,
        product_name=user.product_name,
        created_at=user.created_at,
        stages=stages,
        events=[
            ClientEventResponse(
                id=e.id,
                title=e.title,
                date=e.date,
                description=e.description,
                image_url=e.image_url,
            )
            for e in events
        ],
    )


@admin_router.patch("/clients/{client_id}", response_model=AdminClientUpdatedResponse)
async def update_client(
    client_id: UUID,
    body: UpdateClientBody,
    _admin: AuthUser = Depends(require_admin),
    use_case: UpdateClient = Depends(_update_client),
) -> AdminClientUpdatedResponse:
    inp = UpdateClientInput(
        client_id=client_id,
        name=body.name,
        phone=body.phone,
        description=body.description,
        product_id=body.product_id if "product_id" in body.model_fields_set else None,
        set_product="product_id" in body.model_fields_set,
        stage_ids=tuple(body.stage_ids) if body.stage_ids is not None else None,
    )
    try:
        user = await use_case.execute(inp)
    except UserNotFound as exc:
        raise AppException("CLIENT_NOT_FOUND", str(exc), 404) from exc
    except ProductNotFound as exc:
        raise AppException("PRODUCT_NOT_FOUND", str(exc), 404) from exc
    except DomainError as exc:
        raise AppException("VALIDATION_ERROR", str(exc), 400) from exc

    return AdminClientUpdatedResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        phone=user.phone,
        description=user.description,
        product_id=user.product_id,
        product_name=user.product_name,
        photo_url=user.photo_url,
    )


@admin_router.delete("/clients/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(
    client_id: UUID,
    _admin: AuthUser = Depends(require_admin),
    use_case: DeleteClient = Depends(_delete_client),
) -> None:
    try:
        await use_case.execute(DeleteClientInput(client_id=client_id))
    except UserNotFound as exc:
        raise AppException("CLIENT_NOT_FOUND", str(exc), 404) from exc
    except SupabaseAdminError as exc:
        raise AppException("INTERNAL_ERROR", str(exc), 502) from exc


@admin_router.post("/clients/{client_id}/photo", response_model=PhotoUrlResponse)
async def upload_client_photo(
    client_id: UUID,
    photo: UploadFile = File(...),
    _admin: AuthUser = Depends(require_admin),
    use_case: UploadPhoto = Depends(_upload_client_photo),
) -> PhotoUrlResponse:
    data = await photo.read()
    inp = UploadPhotoInput(
        user_id=client_id,
        content_type=photo.content_type or "",
        data=data,
    )
    try:
        result = await use_case.execute(inp)
    except InvalidPhoto as exc:
        raise AppException("VALIDATION_ERROR", str(exc), 400) from exc
    except UserNotFound as exc:
        raise AppException("CLIENT_NOT_FOUND", str(exc), 404) from exc
    return PhotoUrlResponse(photo_url=result.photo_url)
