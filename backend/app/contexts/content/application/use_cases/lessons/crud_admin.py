from uuid import UUID, uuid4

from app.contexts.content.domain.entities import Lesson
from app.contexts.content.domain.exceptions import LessonNotFound
from app.contexts.content.domain.repositories import LessonRepository
from app.contexts.content.domain.rules import parse_drive_file_id
from app.shared.utils import now_sp


class CreateLesson:
    def __init__(self, repo: LessonRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        module_id: UUID,
        title: str,
        description: str | None,
        drive_url: str,
        duration_minutes: int | None,
        order: int,
    ) -> Lesson:
        drive_file_id = parse_drive_file_id(drive_url)
        lesson = Lesson(
            id=uuid4(),
            module_id=module_id,
            title=title,
            description=description,
            drive_file_id=drive_file_id,
            duration_minutes=duration_minutes,
            order=order,
            created_at=now_sp(),
        )
        return await self._repo.create(lesson)


class UpdateLesson:
    def __init__(self, repo: LessonRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        lesson_id: UUID,
        title: str | None,
        description: str | None,
        drive_url: str | None,
        duration_minutes: int | None,
        order: int | None,
    ) -> Lesson:
        lesson = await self._repo.get_by_id(lesson_id)
        if lesson is None:
            raise LessonNotFound(f"Aula {lesson_id} não encontrada.")

        drive_file_id = parse_drive_file_id(drive_url) if drive_url else lesson.drive_file_id

        updated = Lesson(
            id=lesson.id,
            module_id=lesson.module_id,
            title=title if title is not None else lesson.title,
            description=description if description is not None else lesson.description,
            drive_file_id=drive_file_id,
            duration_minutes=(
                duration_minutes if duration_minutes is not None else lesson.duration_minutes
            ),
            order=order if order is not None else lesson.order,
            created_at=lesson.created_at,
        )
        return await self._repo.update(updated)


class DeleteLesson:
    def __init__(self, repo: LessonRepository) -> None:
        self._repo = repo

    async def execute(self, lesson_id: UUID) -> None:
        lesson = await self._repo.get_by_id(lesson_id)
        if lesson is None:
            raise LessonNotFound(f"Aula {lesson_id} não encontrada.")
        await self._repo.delete(lesson_id)


class ReorderLessons:
    def __init__(self, repo: LessonRepository) -> None:
        self._repo = repo

    async def execute(self, orders: list[tuple[UUID, int]]) -> None:
        await self._repo.reorder(orders)
