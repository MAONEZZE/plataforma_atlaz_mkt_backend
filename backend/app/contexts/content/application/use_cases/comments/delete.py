from uuid import UUID

from app.contexts.content.domain.exceptions import (
    CommentNotFound,
    CommentNotOwnedByUser,
)
from app.contexts.content.domain.repositories import CommentRepository


class DeleteComment:
    def __init__(self, repo: CommentRepository) -> None:
        self._repo = repo

    async def execute(self, comment_id: UUID, user_id: UUID, is_admin: bool) -> None:
        comment = await self._repo.get_by_id(comment_id)
        if comment is None:
            raise CommentNotFound(f"Comentário {comment_id} não encontrado.")

        if not is_admin and comment.user_id != user_id:
            raise CommentNotOwnedByUser("Sem permissão para apagar este comentário.")

        await self._repo.delete_comment(comment_id)
