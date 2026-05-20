from uuid import UUID

from fastapi import APIRouter, Depends, Query
from starlette import status

from app.contexts.auth.domain.entities import User
from app.contexts.content.application.use_cases.comments.delete import DeleteComment
from app.contexts.content.application.use_cases.comments.create import CreateComment
from app.contexts.content.application.use_cases.comments.edit import EditComment
from app.contexts.content.application.use_cases.comments.list import ListComments
from app.contexts.content.domain.exceptions import (
    CommentNotFound,
    ComentarioNaoPertenceAoUsuario,
)
from app.contexts.content.presentation.deps import (
    get_delete_comment,
    get_create_comment,
    get_edit_comment,
    get_list_comments,
)
from app.contexts.content.presentation.schemas import (
    AutorOut,
    ComentarioOut,
    CreateCommentIn,
    EditCommentIn,
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
    user: User = Depends(get_current_user),
    use_case: ListComments = Depends(get_list_comments),
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
    body: CreateCommentIn,
    user: User = Depends(get_current_user),
    use_case: CreateComment = Depends(get_create_comment),
) -> CommentOut:
    from app.contexts.content.domain.exceptions import LessonNotFound

    try:
        comentario = await use_case.execute(aula_id, user.id, body.texto)
    except LessonNotFound as exc:
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
    body: EditCommentIn,
    user: User = Depends(get_current_user),
    use_case: EditComment = Depends(get_edit_comment),
) -> CommentOut:
    try:
        comentario = await use_case.execute(
            comentario_id, user.id, user.role == "admin", body.texto
        )
    except CommentNotFound as exc:
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
    user: User = Depends(get_current_user),
    use_case: DeleteComment = Depends(get_delete_comment),
) -> None:
    try:
        await use_case.execute(comentario_id, user.id, user.role == "admin")
    except CommentNotFound as exc:
        raise AppException("COMENTARIO_NOT_FOUND", str(exc), 404) from exc
    except ComentarioNaoPertenceAoUsuario as exc:
        raise AppException("FORBIDDEN", str(exc), 403) from exc
