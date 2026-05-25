from uuid import UUID

from app.api.controllers.content_module.content_dto.content_dto import (
    LessonSummaryDTO,
    ModuleWithLessonsDTO,
    TrackWithModulesDTO,
)
from app.domain.content_module.content_exceptions import TrackNotFound
from app.domain.content_module.content_repo_interface import (
    LessonRepository,
    ModuleRepository,
    StudentLessonRepository,
    TrackRepository,
)


class GetTrackWithModules:
    def __init__(
        self,
        track_repo: TrackRepository,
        module_repo: ModuleRepository,
        lesson_repo: LessonRepository,
        student_lesson_repo: StudentLessonRepository,
    ) -> None:
        self._track_repo = track_repo
        self._module_repo = module_repo
        self._lesson_repo = lesson_repo
        self._student_lesson_repo = student_lesson_repo

    async def execute(self, track_id: UUID, user_id: UUID) -> TrackWithModulesDTO:
        track = await self._track_repo.get_by_id(track_id)
        if track is None:
            raise TrackNotFound(f"Trilha {track_id} não encontrada.")

        completeds = await self._student_lesson_repo.completed_ids(user_id)
        modules = await self._module_repo.list_by_track(track_id)

        total_lessons = 0
        completeds_count = 0
        modules_dto = []

        for module in modules:
            lessons = await self._lesson_repo.list_by_module(module.id)
            total_lessons += len(lessons)
            completeds_count += sum(1 for a in lessons if a.id in completeds)

            modules_dto.append(
                ModuleWithLessonsDTO(
                    id=module.id,
                    title=module.title,
                    description=module.description,
                    order=module.order,
                    lessons=[
                        LessonSummaryDTO(
                            id=a.id,
                            title=a.title,
                            duration_minutes=a.duration_minutes,
                            order=a.order,
                            completed=a.id in completeds,
                        )
                        for a in lessons
                    ],
                )
            )

        pct = round(completeds_count / total_lessons * 100, 2) if total_lessons > 0 else 0.0

        return TrackWithModulesDTO(
            id=track.id,
            title=track.title,
            description=track.description,
            cover_url=track.cover_url,
            progress_pct=pct,
            modules=modules_dto,
        )
