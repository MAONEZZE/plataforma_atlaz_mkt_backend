from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.config.dependencies.auth_deps import get_current_user
from app.api.controllers.community_module.community_dto.community_dto import (
    CommunityMemberSchema,
    ListCommunityResponse,
)
from app.database.community_module.community_repo import SqlAlchemyCommunityRepository
from app.database.shared.db_factory import get_session
from app.domain.auth_module.auth_model import User as AuthUser
from app.services.community_module.list_community import ListCommunity

router = APIRouter(prefix="/community", tags=["community"])


def _get_list_community(
    session: AsyncSession = Depends(get_session),
) -> ListCommunity:
    return ListCommunity(repo=SqlAlchemyCommunityRepository(session))


@router.get("", response_model=ListCommunityResponse)
async def list_community(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=24, ge=1, le=100),
    _user: AuthUser = Depends(get_current_user),
    use_case: ListCommunity = Depends(_get_list_community),
) -> ListCommunityResponse:
    result = await use_case.execute(page=page, page_size=page_size)
    return ListCommunityResponse(
        items=[
            CommunityMemberSchema(
                id=item.id,
                name=item.name,
                photo_url=item.photo_url,
                linkedin_url=item.linkedin_url,
                instagram_username=item.instagram_username,
                description=item.description,
            )
            for item in result.items
        ],
        page=result.page,
        page_size=result.page_size,
        total=result.total,
    )
