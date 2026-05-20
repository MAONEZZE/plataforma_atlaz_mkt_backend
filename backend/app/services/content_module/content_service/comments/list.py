from uuid import UUID

from app.api.controllers.content_module.content_dto.content_dto import AuthorDTO, CommentDTO
from app.domain.content_module.content_repo_interface import CommentRepository
from app.shared.application.dtos import PagedResponse


class ListComments:
    def __init__(self, repo: CommentRepository) -> None:
        self._repo = repo

    async def execute(
        self, lesson_id: UUID, page: int, page_size: int, current_user_id: UUID
    ) -> PagedResponse[CommentDTO]:
        items, total = await self._repo.list_by_lesson(lesson_id, page, page_size)
        dtos = [
            CommentDTO(
                id=c.id,
                author=AuthorDTO(id=c.user_id, name=c.author_name, photo_url=c.author_photo_url),
                text=c.text,
                created_at=c.created_at,
                edited_at=c.edited_at,
                deleted_at=c.deleted_at,
                is_own=c.user_id == current_user_id,
            )
            for c in items
        ]
        return PagedResponse(items=dtos, page=page, page_size=page_size, total=total)
