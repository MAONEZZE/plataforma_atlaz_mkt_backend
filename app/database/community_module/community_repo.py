from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.community_module.community_model import CommunityMember


class SqlAlchemyCommunityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_active(self, page: int, page_size: int) -> tuple[list[CommunityMember], int]:
        count_result = await self._session.execute(
            text(
                'SELECT COUNT(*) FROM "ATZ_HUB".users WHERE role = \'cliente\' AND inactive = false'
            )
        )
        total: int = count_result.scalar_one()

        offset = (page - 1) * page_size
        rows_result = await self._session.execute(
            text(
                "SELECT u.id, u.name, u.photo_url, u.linkedin_url, u.instagram_username, u.description, p.name as product_name "
                'FROM "ATZ_HUB".users u '
                'LEFT JOIN "ATZ_HUB".products p ON u.product_id = p.id '
                "WHERE u.role = 'cliente' AND u.inactive = false "
                "ORDER BY u.name ASC "
                "LIMIT :limit OFFSET :offset"
            ).bindparams(limit=page_size, offset=offset)
        )
        membros = [
            CommunityMember(
                id=UUID(str(row["id"])),
                name=str(row["name"]),
                photo_url=str(row["photo_url"]) if row["photo_url"] is not None else None,
                linkedin_url=(
                    str(row["linkedin_url"]) if row["linkedin_url"] is not None else None
                ),
                instagram_username=(
                    str(row["instagram_username"])
                    if row["instagram_username"] is not None
                    else None
                ),
                description=str(row["description"]) if row["description"] is not None else None,
                product_name=str(row["product_name"]) if row["product_name"] is not None else None,
            )
            for row in rows_result.mappings()
        ]
        return membros, total
