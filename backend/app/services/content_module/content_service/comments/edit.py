from uuid import UUID

from app.domain.content_module.content_exceptions import (
    CommentNotFound,
    CommentNotOwnedByUser,
)
from app.domain.content_module.content_model import Comment
from app.domain.content_module.content_repo_interface import CommentRepository
from app.shared.utils import now_sp


class EditComment:
    def __init__(self, repo: CommentRepository) -> None:
        self._repo = repo

    async def execute(
        self, comment_id: UUID, user_id: UUID, is_admin: bool, text: str
    ) -> Comment:
        comment = await self._repo.get_by_id(comment_id)
        if comment is None:
            raise CommentNotFound(f"Comentário {comment_id} não encontrado.")

        if not is_admin and comment.user_id != user_id:
            raise CommentNotOwnedByUser("Sem permissão para editar este comentário.")

        updated = Comment(
            id=comment.id,
            lesson_id=comment.lesson_id,
            user_id=comment.user_id,
            text=text,
            created_at=comment.created_at,
            edited_at=now_sp(),
            deleted_at=comment.deleted_at,
        )
        return await self._repo.update(updated)
