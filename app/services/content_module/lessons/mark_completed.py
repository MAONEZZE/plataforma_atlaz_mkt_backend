from uuid import UUID

from app.domain.content_module.content_exceptions import LessonNotFound
from app.domain.content_module.content_repo_interface import (
    LessonRepository,
    StudentLessonRepository,
)


class MarkCompleted:
    def __init__(self, lesson_repo: LessonRepository, student_lesson_repo: StudentLessonRepository) -> None:
        self._lesson_repo = lesson_repo
        self._student_lesson_repo = student_lesson_repo

    async def execute(self, lesson_id: UUID, user_id: UUID) -> None:
        lesson = await self._lesson_repo.get_by_id(lesson_id)
        if lesson is None:
            raise LessonNotFound(f"Aula {lesson_id} não encontrada.")
        await self._student_lesson_repo.mark_completed(user_id, lesson_id)
