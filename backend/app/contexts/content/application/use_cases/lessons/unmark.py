from uuid import UUID

from app.contexts.content.domain.repositories import StudentLessonRepository


class Unmark:
    def __init__(self, student_lesson_repo: StudentLessonRepository) -> None:
        self._student_lesson_repo = student_lesson_repo

    async def execute(self, lesson_id: UUID, user_id: UUID) -> None:
        await self._student_lesson_repo.unmark(user_id, lesson_id)
