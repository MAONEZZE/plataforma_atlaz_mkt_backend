from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.config.dependencies.auth_deps import require_admin
from app.api.controllers.user_module.user_dto.user_dto import (
    ClientSummaryResponse,
    CreateClientBody,
    ListClientsResponse,
    UserResponse,
)
from app.database.product_module.product_repo import SqlAlchemyProductRepository
from app.database.shared.db_factory import get_session
from app.database.shared.supabase_client import create_supabase_admin_client
from app.database.user_module.user_repo import SqlAlchemyUserRepository
from app.domain.auth_module.auth_model import User as AuthUser
from app.domain.shared.base_exceptions import AppException, DomainError
from app.domain.user_module.user_exceptions import (
    EmailAlreadyRegistered,
    SupabaseAdminError,
    UserTriggerSyncFailed,
)
from app.services.user_module.create_client_service import (
    CreateClient,
    CreateClientInput,
)
from app.services.user_module.list_clients_service import (
    ListClients,
    ListClientsInput,
)
from app.services.user_module.supabase_admin_gateway import (
    SupabaseAdminUserGatewayImpl,
)

admin_router = APIRouter(prefix="/admin", tags=["admin-clients"])


def _create_client(session: AsyncSession = Depends(get_session)) -> CreateClient:
    gateway = SupabaseAdminUserGatewayImpl(create_supabase_admin_client())
    return CreateClient(
        repo=SqlAlchemyUserRepository(session),
        gateway=gateway,
        product_repo=SqlAlchemyProductRepository(session),
    )


def _list_clients(session: AsyncSession = Depends(get_session)) -> ListClients:
    return ListClients(repo=SqlAlchemyUserRepository(session))


@admin_router.post(
    "/clients",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_client(
    body: CreateClientBody,
    _admin: AuthUser = Depends(require_admin),
    use_case: CreateClient = Depends(_create_client),
) -> UserResponse:
    inp = CreateClientInput(
        name=body.name,
        email=body.email,
        password=body.password,
        phone=body.phone,
        product_id=body.product_id,
    )
    try:
        user = await use_case.execute(inp)
    except EmailAlreadyRegistered as exc:
        raise AppException("EMAIL_ALREADY_REGISTERED", str(exc), 409) from exc
    except UserTriggerSyncFailed as exc:
        raise AppException("INTERNAL_ERROR", str(exc), 500) from exc
    except SupabaseAdminError as exc:
        raise AppException("INTERNAL_ERROR", str(exc), 502) from exc
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
        product_id=user.product_id,
        created_at=user.created_at,
    )


@admin_router.get("/clients", response_model=ListClientsResponse)
async def list_clients(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    _admin: AuthUser = Depends(require_admin),
    use_case: ListClients = Depends(_list_clients),
) -> ListClientsResponse:
    items, total = await use_case.execute(
        ListClientsInput(page=page, page_size=page_size)
    )
    return ListClientsResponse(
        items=[ClientSummaryResponse.model_validate(u) for u in items],
        page=page,
        page_size=page_size,
        total=total,
    )
