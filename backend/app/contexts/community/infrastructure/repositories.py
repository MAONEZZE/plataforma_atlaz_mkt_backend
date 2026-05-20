from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.contexts.community.domain.entities import CommunityMember


class SqlAlchemyCommunityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_active(self, page: int, page_size: int) -> tuple[list[CommunityMember], int]:
        count_result = await self._session.execute(
            text(
                "SELECT COUNT(*) FROM public.users " "WHERE role = 'cliente' AND inativo = false"
            )
        )
        total: int = count_result.scalar_one()

        offset = (page - 1) * page_size
        rows_result = await self._session.execute(
            text(
                "SELECT id, nome, foto_url, linkedin_url, instagram_username "
                "FROM public.users "
                "WHERE role = 'cliente' AND inativo = false "
                "ORDER BY name ASC "
                "LIMIT :limit OFFSET :offset"
            ).bindparams(limit=page_size, offset=offset)
        )
        membros = [
            CommunityMember(
                id=UUID(str(row["id"])),
                nome=str(row["nome"]),
                foto_url=str(row["foto_url"]) if row["foto_url"] is not None else None,
                linkedin_url=(
                    str(row["linkedin_url"]) if row["linkedin_url"] is not None else None
                ),
                instagram_username=(
                    str(row["instagram_username"])
                    if row["instagram_username"] is not None
                    else None
                ),
            )
            for row in rows_result.mappings()
        ]
        return membros, total
