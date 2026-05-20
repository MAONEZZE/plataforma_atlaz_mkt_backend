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
    CommentNotOwnedByUser,
)
from app.contexts.content.presentation.deps import (
    get_delete_comment,
    get_create_comment,
    get_edit_comment,
    get_list_comments,
)
from app.contexts.content.presentation.schemas import (
    AuthorOut,
    CommentOut,
    CreateCommentIn,
    EditCommentIn,
)
from app.core.deps import get_current_user
from app.core.exceptions import AppException
from app.shared.application.dtos import PagedResponse

router = APIRouter(tags=["comments"])


@router.get("/lessons/{lesson_id}/comments", response_model=PagedResponse[CommentOut])
async def list_comments(
    lesson_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    use_case: ListComments = Depends(get_list_comments),
) -> PagedResponse[CommentOut]:
    result = await use_case.execute(lesson_id, page, page_size, user.id)
    return PagedResponse(
        items=[
            CommentOut(
                id=c.id,
                author=AuthorOut(id=c.author.id, name=c.author.name, photo_url=c.author.photo_url),
                text=c.text,
                created_at=c.created_at,
                edited_at=c.edited_at,
                deleted_at=c.deleted_at,
                is_own=c.is_own,
            )
            for c in result.items
        ],
        page=result.page,
        page_size=result.page_size,
        total=result.total,
    )


@router.post(
    "/lessons/{lesson_id}/comments",
    response_model=CommentOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_comment(
    lesson_id: UUID,
    body: CreateCommentIn,
    user: User = Depends(get_current_user),
    use_case: CreateComment = Depends(get_create_comment),
) -> CommentOut:
    from app.contexts.content.domain.exceptions import LessonNotFound

    try:
        comment = await use_case.execute(lesson_id, user.id, body.text)
    except LessonNotFound as exc:
        raise AppException("AULA_NOT_FOUND", str(exc), 404) from exc

    return CommentOut(
        id=comment.id,
        author=AuthorOut(id=user.id, name="", photo_url=None),
        text=comment.text,
        created_at=comment.created_at,
        edited_at=comment.edited_at,
        deleted_at=comment.deleted_at,
        is_own=True,
    )


@router.patch("/comments/{comment_id}", response_model=CommentOut)
async def edit_comment(
    comment_id: UUID,
    body: EditCommentIn,
    user: User = Depends(get_current_user),
    use_case: EditComment = Depends(get_edit_comment),
) -> CommentOut:
    try:
        comment = await use_case.execute(
            comment_id, user.id, user.role == "admin", body.text
        )
    except CommentNotFound as exc:
        raise AppException("COMENTARIO_NOT_FOUND", str(exc), 404) from exc
    except CommentNotOwnedByUser as exc:
        raise AppException("FORBIDDEN", str(exc), 403) from exc
    return CommentOut(
        id=comment.id,
        author=AuthorOut(id=user.id, name="", photo_url=None),
        text=comment.text,
        created_at=comment.created_at,
        edited_at=comment.edited_at,
        deleted_at=comment.deleted_at,
        is_own=True,
    )


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: UUID,
    user: User = Depends(get_current_user),
    use_case: DeleteComment = Depends(get_delete_comment),
) -> None:
    try:
        await use_case.execute(comment_id, user.id, user.role == "admin")
    except CommentNotFound as exc:
        raise AppException("COMENTARIO_NOT_FOUND", str(exc), 404) from exc
    except CommentNotOwnedByUser as exc:
        raise AppException("FORBIDDEN", str(exc), 403) from exc
