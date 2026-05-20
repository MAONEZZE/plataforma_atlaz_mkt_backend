from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.contexts.auth.domain.entities import User
from app.contexts.community.application.use_cases.list_community import ListCommunity
from app.contexts.community.infrastructure.repositories import SqlAlchemyCommunityRepository
from app.contexts.community.presentation.schemas import (
    ListCommunityResponse,
    CommunityMemberSchema,
)
from app.core.db import get_session
from app.core.deps import get_current_user

router = APIRouter(prefix="/community", tags=["community"])


def _get_list_community(
    session: AsyncSession = Depends(get_session),
) -> ListCommunity:
    return ListCommunity(repo=SqlAlchemyCommunityRepository(session))


@router.get("", response_model=ListCommunityResponse)
async def list_community(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=24, ge=1, le=100),
    _user: User = Depends(get_current_user),
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
            )
            for item in result.items
        ],
        page=result.page,
        page_size=result.page_size,
        total=result.total,
    )
