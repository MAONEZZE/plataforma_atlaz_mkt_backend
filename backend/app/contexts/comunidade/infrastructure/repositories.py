from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.contexts.comunidade.domain.entities import MembroComunidade


class SqlAlchemyComunidadeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def listar_ativos(self, page: int, page_size: int) -> tuple[list[MembroComunidade], int]:
        count_result = await self._session.execute(
            text(
                "SELECT COUNT(*) FROM public.usuario " "WHERE role = 'cliente' AND inativo = false"
            )
        )
        total: int = count_result.scalar_one()

        offset = (page - 1) * page_size
        rows_result = await self._session.execute(
            text(
                "SELECT id, nome, foto_url, linkedin_url, instagram_username "
                "FROM public.usuario "
                "WHERE role = 'cliente' AND inativo = false "
                "ORDER BY nome ASC "
                "LIMIT :limit OFFSET :offset"
            ).bindparams(limit=page_size, offset=offset)
        )
        membros = [
            MembroComunidade(
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
