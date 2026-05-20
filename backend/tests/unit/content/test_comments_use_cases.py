from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from app.contexts.content.application.use_cases.comments.delete import DeleteComment
from app.contexts.content.application.use_cases.comments.create import CreateComment
from app.contexts.content.application.use_cases.comments.edit import EditComment
from app.contexts.content.application.use_cases.comments.list import ListComments
from app.contexts.content.domain.entities import Lesson, Comment, CommentRead
from app.contexts.content.domain.exceptions import (
    LessonNotFound,
    CommentNotFound,
    CommentNotOwnedByUser,
)
from app.shared.application.dtos import PagedResponse


# ── Fake repos ─────────────────────────────────────────────────────────────────

class FakeLessonRepo:
    def __init__(self, lesson: Lesson | None = None) -> None:
        self._lesson = lesson

    async def get_by_id(self, lesson_id: UUID) -> Lesson | None:
        return self._lesson if self._lesson and self._lesson.id == lesson_id else None


class FakeCommentRepo:
    def __init__(self, comments: list[Comment] | None = None) -> None:
        self._comments: list[Comment] = comments or []
        self._deleted: list[UUID] = []

    async def list_by_lesson(
        self, lesson_id: UUID, page: int, page_size: int
    ) -> tuple[list[CommentRead], int]:
        items = [c for c in self._comments if c.lesson_id == lesson_id]
        total = len(items)
        offset = (page - 1) * page_size
        page_items = items[offset : offset + page_size]
        reads = [
            CommentRead(
                id=c.id,
                lesson_id=c.lesson_id,
                user_id=c.user_id,
                text=None if c.deleted_at else c.text,
                created_at=c.created_at,
                edited_at=c.edited_at,
                deleted_at=c.deleted_at,
                author_name="Author",
                author_photo_url=None,
            )
            for c in page_items
        ]
        return reads, total

    async def get_by_id(self, comment_id: UUID) -> Comment | None:
        return next((c for c in self._comments if c.id == comment_id), None)

    async def create(self, comment: Comment) -> Comment:
        self._comments.append(comment)
        return comment

    async def update(self, comment: Comment) -> Comment:
        self._comments = [comment if c.id == comment.id else c for c in self._comments]
        return comment

    async def delete_comment(self, comment_id: UUID) -> None:
        self._deleted.append(comment_id)


def _make_lesson() -> Lesson:
    return Lesson(
        id=uuid4(), module_id=uuid4(), title="Lesson", description=None,
        drive_file_id="x", duration_minutes=None, order=0, created_at=datetime.now(tz=UTC)
    )


def _make_comment(user_id: UUID, lesson_id: UUID, text: str = "Text") -> Comment:
    return Comment(
        id=uuid4(),
        lesson_id=lesson_id,
        user_id=user_id,
        text=text,
        created_at=datetime.now(tz=UTC),
        edited_at=None,
        deleted_at=None,
    )


# ── CreateComment ────────────────────────────────────────────────────────────

async def test_create_comment_ok() -> None:
    lesson = _make_lesson()
    comment_repo = FakeCommentRepo()
    use_case = CreateComment(FakeLessonRepo(lesson), comment_repo)
    c = await use_case.execute(lesson.id, uuid4(), "Great lesson!")
    assert c.text == "Great lesson!"
    assert len(comment_repo._comments) == 1


async def test_create_comment_lesson_not_found_raises() -> None:
    use_case = CreateComment(FakeLessonRepo(None), FakeCommentRepo())
    with pytest.raises(LessonNotFound):
        await use_case.execute(uuid4(), uuid4(), "text")


# ── EditComment ───────────────────────────────────────────────────────────

async def test_edit_own_comment() -> None:
    user_id = uuid4()
    lesson_id = uuid4()
    comment = _make_comment(user_id, lesson_id)
    repo = FakeCommentRepo([comment])
    use_case = EditComment(repo)
    updated = await use_case.execute(comment.id, user_id, False, "New text")
    assert updated.text == "New text"
    assert updated.edited_at is not None


async def test_edit_other_user_comment_raises() -> None:
    other_id = uuid4()
    comment = _make_comment(uuid4(), uuid4())
    repo = FakeCommentRepo([comment])
    use_case = EditComment(repo)
    with pytest.raises(CommentNotOwnedByUser):
        await use_case.execute(comment.id, other_id, False, "hack")


async def test_edit_comment_admin_can_edit_any() -> None:
    comment = _make_comment(uuid4(), uuid4())
    repo = FakeCommentRepo([comment])
    use_case = EditComment(repo)
    updated = await use_case.execute(comment.id, uuid4(), True, "Admin edit")
    assert updated.text == "Admin edit"


async def test_edit_comment_not_found_raises() -> None:
    use_case = EditComment(FakeCommentRepo())
    with pytest.raises(CommentNotFound):
        await use_case.execute(uuid4(), uuid4(), False, "text")


# ── DeleteComment ───────────────────────────────────────────────────────────

async def test_delete_own_comment() -> None:
    user_id = uuid4()
    comment = _make_comment(user_id, uuid4())
    repo = FakeCommentRepo([comment])
    use_case = DeleteComment(repo)
    await use_case.execute(comment.id, user_id, False)
    assert comment.id in repo._deleted


async def test_delete_other_user_comment_raises() -> None:
    comment = _make_comment(uuid4(), uuid4())
    repo = FakeCommentRepo([comment])
    use_case = DeleteComment(repo)
    with pytest.raises(CommentNotOwnedByUser):
        await use_case.execute(comment.id, uuid4(), False)


async def test_delete_comment_admin_can_delete_any() -> None:
    comment = _make_comment(uuid4(), uuid4())
    repo = FakeCommentRepo([comment])
    use_case = DeleteComment(repo)
    await use_case.execute(comment.id, uuid4(), True)
    assert comment.id in repo._deleted


async def test_delete_comment_not_found_raises() -> None:
    use_case = DeleteComment(FakeCommentRepo())
    with pytest.raises(CommentNotFound):
        await use_case.execute(uuid4(), uuid4(), False)


# ── ListComments ──────────────────────────────────────────────────────────

async def test_list_comments_is_own_flag() -> None:
    current_user = uuid4()
    lesson_id = uuid4()
    own = _make_comment(current_user, lesson_id)
    other = _make_comment(uuid4(), lesson_id)
    repo = FakeCommentRepo([own, other])
    use_case = ListComments(repo)
    result: PagedResponse = await use_case.execute(lesson_id, 1, 20, current_user)
    by_id = {c.id: c for c in result.items}
    assert by_id[own.id].is_own is True
    assert by_id[other.id].is_own is False


async def test_list_comments_deleted_text_is_null() -> None:
    current_user = uuid4()
    lesson_id = uuid4()
    deleted = Comment(
        id=uuid4(), lesson_id=lesson_id, user_id=uuid4(), text="secret",
        created_at=datetime.now(tz=UTC), edited_at=None, deleted_at=datetime.now(tz=UTC),
    )
    repo = FakeCommentRepo([deleted])
    use_case = ListComments(repo)
    result = await use_case.execute(lesson_id, 1, 20, current_user)
    assert result.items[0].text is None


async def test_list_comments_pagination() -> None:
    current_user = uuid4()
    lesson_id = uuid4()
    comments = [_make_comment(uuid4(), lesson_id) for _ in range(5)]
    repo = FakeCommentRepo(comments)
    use_case = ListComments(repo)
    result = await use_case.execute(lesson_id, 1, 3, current_user)
    assert result.total == 5
    assert len(result.items) == 3
    assert result.page == 1
    assert result.page_size == 3
