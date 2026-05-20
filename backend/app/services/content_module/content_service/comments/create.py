from uuid import UUID, uuid4

from app.domain.content_module.content_exceptions import LessonNotFound
from app.domain.content_module.content_model import Comment
from app.domain.content_module.content_repo_interface import CommentRepository, LessonRepository
from app.domain.shared.utils import now_sp


class CreateComment:
    def __init__(self, lesson_repo: LessonRepository, comment_repo: CommentRepository) -> None:
        self._lesson_repo = lesson_repo
        self._comment_repo = comment_repo

    async def execute(self, lesson_id: UUID, user_id: UUID, text: str) -> Comment:
        lesson = await self._lesson_repo.get_by_id(lesson_id)
        if lesson is None:
            raise LessonNotFound(f"Aula {lesson_id} não encontrada.")

        comment = Comment(
            id=uuid4(),
            lesson_id=lesson_id,
            user_id=user_id,
            text=text,
            created_at=now_sp(),
            edited_at=None,
            deleted_at=None,
        )
        return await self._comment_repo.create(comment)
