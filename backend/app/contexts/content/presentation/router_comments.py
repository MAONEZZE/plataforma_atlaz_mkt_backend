from uuid import UUID

from fastapi import APIRouter, Depends, Query
from starlette import status

from app.contexts.auth.domain.entities import Usuario
from app.contexts.conteudo.application.use_cases.comentarios.apagar import ApagarComentario
from app.contexts.conteudo.application.use_cases.comentarios.criar import CriarComentario
from app.contexts.conteudo.application.use_cases.comentarios.editar import EditarComentario
from app.contexts.conteudo.application.use_cases.comentarios.listar import ListarComentarios
from app.contexts.conteudo.domain.exceptions import (
    ComentarioNaoEncontrado,
    ComentarioNaoPertenceAoUsuario,
)
from app.contexts.conteudo.presentation.deps import (
    get_apagar_comentario,
    get_criar_comentario,
    get_editar_comentario,
    get_listar_comentarios,
)
from app.contexts.conteudo.presentation.schemas import (
    AutorOut,
    ComentarioOut,
    CriarComentarioIn,
    EditarComentarioIn,
)
from app.core.deps import get_current_user
from app.core.exceptions import AppException
from app.shared.application.dtos import PagedResponse

router = APIRouter(tags=["comentarios"])


@router.get("/aulas/{aula_id}/comentarios", response_model=PagedResponse[ComentarioOut])
async def listar_comentarios(
    aula_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: Usuario = Depends(get_current_user),
    use_case: ListarComentarios = Depends(get_listar_comentarios),
) -> PagedResponse[ComentarioOut]:
    result = await use_case.execute(aula_id, page, page_size, user.id)
    return PagedResponse(
        items=[
            ComentarioOut(
                id=c.id,
                autor=AutorOut(id=c.autor.id, nome=c.autor.nome, foto_url=c.autor.foto_url),
                texto=c.texto,
                criado_em=c.criado_em,
                editado_em=c.editado_em,
                apagado_em=c.apagado_em,
                is_proprio=c.is_proprio,
            )
            for c in result.items
        ],
        page=result.page,
        page_size=result.page_size,
        total=result.total,
    )


@router.post(
    "/aulas/{aula_id}/comentarios",
    response_model=ComentarioOut,
    status_code=status.HTTP_201_CREATED,
)
async def criar_comentario(
    aula_id: UUID,
    body: CriarComentarioIn,
    user: Usuario = Depends(get_current_user),
    use_case: CriarComentario = Depends(get_criar_comentario),
) -> ComentarioOut:
    from app.contexts.conteudo.domain.exceptions import AulaNaoEncontrada

    try:
        comentario = await use_case.execute(aula_id, user.id, body.texto)
    except AulaNaoEncontrada as exc:
        raise AppException("AULA_NOT_FOUND", str(exc), 404) from exc

    # For the created response we don't have autor_nome from the entity — use user.id as placeholder
    # The list endpoint does the join; here we return minimal data
    return ComentarioOut(
        id=comentario.id,
        autor=AutorOut(id=user.id, nome="", foto_url=None),
        texto=comentario.texto,
        criado_em=comentario.criado_em,
        editado_em=comentario.editado_em,
        apagado_em=comentario.apagado_em,
        is_proprio=True,
    )


@router.patch("/comentarios/{comentario_id}", response_model=ComentarioOut)
async def editar_comentario(
    comentario_id: UUID,
    body: EditarComentarioIn,
    user: Usuario = Depends(get_current_user),
    use_case: EditarComentario = Depends(get_editar_comentario),
) -> ComentarioOut:
    try:
        comentario = await use_case.execute(
            comentario_id, user.id, user.role == "admin", body.texto
        )
    except ComentarioNaoEncontrado as exc:
        raise AppException("COMENTARIO_NOT_FOUND", str(exc), 404) from exc
    except ComentarioNaoPertenceAoUsuario as exc:
        raise AppException("FORBIDDEN", str(exc), 403) from exc
    return ComentarioOut(
        id=comentario.id,
        autor=AutorOut(id=user.id, nome="", foto_url=None),
        texto=comentario.texto,
        criado_em=comentario.criado_em,
        editado_em=comentario.editado_em,
        apagado_em=comentario.apagado_em,
        is_proprio=True,
    )


@router.delete("/comentarios/{comentario_id}", status_code=status.HTTP_204_NO_CONTENT)
async def apagar_comentario(
    comentario_id: UUID,
    user: Usuario = Depends(get_current_user),
    use_case: ApagarComentario = Depends(get_apagar_comentario),
) -> None:
    try:
        await use_case.execute(comentario_id, user.id, user.role == "admin")
    except ComentarioNaoEncontrado as exc:
        raise AppException("COMENTARIO_NOT_FOUND", str(exc), 404) from exc
    except ComentarioNaoPertenceAoUsuario as exc:
        raise AppException("FORBIDDEN", str(exc), 403) from exc
