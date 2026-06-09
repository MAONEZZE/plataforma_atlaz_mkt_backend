from uuid import UUID

from app.api.controllers.content_module.content_dto.content_dto import TrackProgressDTO
from app.domain.content_module.content_repo_interface import (
    LessonRepository,
    ModuleRepository,
    StudentLessonRepository,
    TrackRepository,
)


class ListTracksWithProgress:
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

    async def execute(self, user_id: UUID) -> list[TrackProgressDTO]:
        tracks = await self._track_repo.list_all()
        completeds = await self._student_lesson_repo.completed_ids(user_id)

        result = []
        for track in tracks:
            modules = await self._module_repo.list_by_track(track.id)
            all_lessons = []
            for module in modules:
                lessons = await self._lesson_repo.list_by_module(module.id)
                all_lessons.extend(lessons)

            total = len(all_lessons)
            completeds_count = sum(1 for a in all_lessons if a.id in completeds)
            pct = round(completeds_count / total * 100, 2) if total > 0 else 0.0

            result.append(
                TrackProgressDTO(
                    id=track.id,
                    title=track.title,
                    description=track.description,
                    cover_url=track.cover_url,
                    order=track.order,
                    total_lessons=total,
                    lessons_completed=completeds_count,
                    progress_pct=pct,
                )
            )
        return result
