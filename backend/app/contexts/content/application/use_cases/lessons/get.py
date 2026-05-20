from uuid import UUID

from app.contexts.content.application.dtos import LessonDetailDTO, LessonSummaryDTO, TrackSummaryDTO
from app.contexts.content.domain.exceptions import (
    LessonNotFound,
    ModuleNotFound,
    TrackNotFound,
)
from app.contexts.content.domain.repositories import (
    StudentLessonRepository,
    LessonRepository,
    ModuleRepository,
    TrackRepository,
)


class GetLesson:
    def __init__(
        self,
        lesson_repo: LessonRepository,
        module_repo: ModuleRepository,
        track_repo: TrackRepository,
        student_lesson_repo: StudentLessonRepository,
    ) -> None:
        self._lesson_repo = lesson_repo
        self._module_repo = module_repo
        self._track_repo = track_repo
        self._student_lesson_repo = student_lesson_repo

    async def execute(self, lesson_id: UUID, user_id: UUID) -> LessonDetailDTO:
        lesson = await self._lesson_repo.get_by_id(lesson_id)
        if lesson is None:
            raise LessonNotFound(f"Aula {lesson_id} não encontrada.")

        module = await self._module_repo.get_by_id(lesson.module_id)
        if module is None:
            raise ModuleNotFound(f"Módulo {lesson.module_id} não encontrado.")

        track = await self._track_repo.get_by_id(module.track_id)
        if track is None:
            raise TrackNotFound(f"Trilha {module.track_id} não encontrada.")

        completeds = await self._student_lesson_repo.completed_ids(user_id)
        next_lesson = await self._lesson_repo.next_lesson(lesson)

        return LessonDetailDTO(
            id=lesson.id,
            module_id=lesson.module_id,
            title=lesson.title,
            description=lesson.description,
            drive_file_id=lesson.drive_file_id,
            duration_minutes=lesson.duration_minutes,
            completed=lesson.id in completeds,
            track=TrackSummaryDTO(id=track.id, title=track.title),
            next_lesson=(
                LessonSummaryDTO(
                    id=next_lesson.id,
                    title=next_lesson.title,
                    duration_minutes=next_lesson.duration_minutes,
                    order=next_lesson.order,
                    completed=next_lesson.id in completeds,
                )
                if next_lesson
                else None
            ),
        )
