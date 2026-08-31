from uuid import UUID, uuid4

from app.domain.content_module.content_exceptions import LessonNotFound, ModuleNotFound
from app.domain.content_module.content_model import Lesson
from app.domain.content_module.content_repo_interface import LessonRepository, ModuleRepository
from app.domain.content_module.content_validator import parse_drive_file_id
from app.domain.shared.utils import now_sp


class CreateLesson:
    def __init__(self, repo: LessonRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        module_id: UUID,
        title: str,
        description: str | None,
        drive_url: str | None,
        document_url: str | None,
        duration_minutes: int | None,
        order: int,
        is_doc: bool,
    ) -> Lesson:
        if is_doc and document_url:
            content_id = document_url
        elif not is_doc and drive_url:
            content_id = parse_drive_file_id(drive_url)
        else:
            raise ValueError("drive_url required when is_doc=False, document_url required when is_doc=True")

        lesson = Lesson(
            id=uuid4(),
            module_id=module_id,
            title=title,
            description=description,
            drive_file_id=content_id,
            duration_minutes=duration_minutes,
            order=order,
            is_doc=is_doc,
            created_at=now_sp(),
        )
        return await self._repo.create(lesson)


class UpdateLesson:
    def __init__(self, repo: LessonRepository, module_repo: ModuleRepository) -> None:
        self._repo = repo
        self._module_repo = module_repo

    async def execute(
        self,
        lesson_id: UUID,
        title: str | None,
        description: str | None,
        drive_url: str | None,
        document_url: str | None,
        duration_minutes: int | None,
        order: int | None,
        is_doc: bool | None,
        module_id: UUID | None = None,
    ) -> Lesson:
        lesson = await self._repo.get_by_id(lesson_id)
        if lesson is None:
            raise LessonNotFound(f"Aula {lesson_id} não encontrada.")

        new_module_id = lesson.module_id
        new_order = order if order is not None else lesson.order
        if module_id is not None and module_id != lesson.module_id:
            if await self._module_repo.get_by_id(module_id) is None:
                raise ModuleNotFound(f"Módulo {module_id} não encontrado.")
            new_module_id = module_id
            # Sem posição explícita, a aula entra no fim do módulo de destino.
            if order is None:
                new_order = len(await self._repo.list_by_module(module_id))

        new_is_doc = is_doc if is_doc is not None else lesson.is_doc

        if document_url:
            drive_file_id = document_url
        elif drive_url:
            drive_file_id = parse_drive_file_id(drive_url)
        else:
            drive_file_id = lesson.drive_file_id

        updated = Lesson(
            id=lesson.id,
            module_id=new_module_id,
            title=title if title is not None else lesson.title,
            description=description if description is not None else lesson.description,
            drive_file_id=drive_file_id,
            duration_minutes=(
                duration_minutes if duration_minutes is not None else lesson.duration_minutes
            ),
            order=new_order,
            is_doc=new_is_doc,
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
