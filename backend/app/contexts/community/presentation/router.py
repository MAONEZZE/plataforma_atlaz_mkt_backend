from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.contexts.auth.domain.entities import Usuario
from app.contexts.comunidade.application.use_cases.listar_comunidade import ListarComunidade
from app.contexts.comunidade.infrastructure.repositories import SqlAlchemyComunidadeRepository
from app.contexts.comunidade.presentation.schemas import (
    ListarComunidadeResponse,
    MembroComunidadeSchema,
)
from app.core.db import get_session
from app.core.deps import get_current_user

router = APIRouter(prefix="/comunidade", tags=["comunidade"])


def _get_listar_comunidade(
    session: AsyncSession = Depends(get_session),
) -> ListarComunidade:
    return ListarComunidade(repo=SqlAlchemyComunidadeRepository(session))


@router.get("", response_model=ListarComunidadeResponse)
async def listar_comunidade(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=24, ge=1, le=100),
    _user: Usuario = Depends(get_current_user),
    use_case: ListarComunidade = Depends(_get_listar_comunidade),
) -> ListarComunidadeResponse:
    result = await use_case.execute(page=page, page_size=page_size)
    return ListarComunidadeResponse(
        items=[
            MembroComunidadeSchema(
                id=item.id,
                nome=item.nome,
                foto_url=item.foto_url,
                linkedin_url=item.linkedin_url,
                instagram_username=item.instagram_username,
            )
            for item in result.items
        ],
        page=result.page,
        page_size=result.page_size,
        total=result.total,
    )
