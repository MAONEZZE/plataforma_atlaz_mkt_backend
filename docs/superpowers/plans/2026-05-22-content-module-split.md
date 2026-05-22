# content_module Split Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split `app/…/content_module` into four independent modules — `tracks_module`, `modules_module`, `lessons_module`, `comments_module` — across all four layers (domain, database, services, controllers).

**Architecture:** Each new module owns its domain models, exceptions, repo interfaces, SQLAlchemy repos, service use-cases, and FastAPI router + DTOs. `app/api/controllers/shared_content/shared_dto.py` holds cross-cutting types (`LessonSummaryDTO/Out`, `TrackSummaryDTO/Out`, `ReorderIn`) to avoid circular imports between `tracks_module` and `lessons_module` controllers.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy async, Pydantic v2, pytest-asyncio.

---

### Task 1: Domain — all four new modules

**Files to create:**
- `app/domain/tracks_module/__init__.py`
- `app/domain/tracks_module/tracks_model.py`
- `app/domain/tracks_module/tracks_exceptions.py`
- `app/domain/tracks_module/tracks_repo_interface.py`
- `app/domain/modules_module/__init__.py`
- `app/domain/modules_module/modules_model.py`
- `app/domain/modules_module/modules_exceptions.py`
- `app/domain/modules_module/modules_repo_interface.py`
- `app/domain/lessons_module/__init__.py`
- `app/domain/lessons_module/lessons_model.py`
- `app/domain/lessons_module/lessons_exceptions.py`
- `app/domain/lessons_module/lessons_repo_interface.py`
- `app/domain/lessons_module/lessons_validator.py`
- `app/domain/comments_module/__init__.py`
- `app/domain/comments_module/comments_model.py`
- `app/domain/comments_module/comments_exceptions.py`
- `app/domain/comments_module/comments_repo_interface.py`

- [ ] **Step 1: Create tracks domain files**

```python
# app/domain/tracks_module/__init__.py
```

```python
# app/domain/tracks_module/tracks_model.py
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class Track:
    id: UUID
    title: str
    description: str | None
    cover_url: str | None
    order: int
    created_at: datetime
```

```python
# app/domain/tracks_module/tracks_exceptions.py
from app.domain.shared.base_exceptions import DomainError


class TrackNotFound(DomainError):
    pass
```

```python
# app/domain/tracks_module/tracks_repo_interface.py
from typing import Protocol
from uuid import UUID

from app.domain.tracks_module.tracks_model import Track


class TrackRepository(Protocol):
    async def list_all(self) -> list[Track]: ...
    async def get_by_id(self, track_id: UUID) -> Track | None: ...
    async def create(self, track: Track) -> Track: ...
    async def update(self, track: Track) -> Track: ...
    async def delete(self, track_id: UUID) -> None: ...
    async def reorder(self, orders: list[tuple[UUID, int]]) -> None: ...
    async def count_lessons(self, track_id: UUID) -> int: ...
```

- [ ] **Step 2: Create modules domain files**

```python
# app/domain/modules_module/__init__.py
```

```python
# app/domain/modules_module/modules_model.py
from dataclasses import dataclass
from uuid import UUID


@dataclass
class Module:
    id: UUID
    track_id: UUID
    title: str
    description: str | None
    order: int
```

```python
# app/domain/modules_module/modules_exceptions.py
from app.domain.shared.base_exceptions import DomainError


class ModuleNotFound(DomainError):
    pass
```

```python
# app/domain/modules_module/modules_repo_interface.py
from typing import Protocol
from uuid import UUID

from app.domain.modules_module.modules_model import Module


class ModuleRepository(Protocol):
    async def list_by_track(self, track_id: UUID) -> list[Module]: ...
    async def get_by_id(self, module_id: UUID) -> Module | None: ...
    async def create(self, module: Module) -> Module: ...
    async def update(self, module: Module) -> Module: ...
    async def delete(self, module_id: UUID) -> None: ...
    async def reorder(self, orders: list[tuple[UUID, int]]) -> None: ...
```

- [ ] **Step 3: Create lessons domain files**

```python
# app/domain/lessons_module/__init__.py
```

```python
# app/domain/lessons_module/lessons_model.py
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class Lesson:
    id: UUID
    module_id: UUID
    title: str
    description: str | None
    drive_file_id: str
    duration_minutes: int | None
    order: int
    created_at: datetime


@dataclass
class StudentLesson:
    user_id: UUID
    lesson_id: UUID
    completed_at: datetime
```

```python
# app/domain/lessons_module/lessons_exceptions.py
from app.domain.shared.base_exceptions import DomainError


class LessonNotFound(DomainError):
    pass


class InvalidDriveUrl(DomainError):
    def __init__(self, url: str) -> None:
        super().__init__(f"URL do Google Drive inválida: {url}")
```

```python
# app/domain/lessons_module/lessons_repo_interface.py
from typing import Protocol
from uuid import UUID

from app.domain.lessons_module.lessons_model import Lesson


class LessonRepository(Protocol):
    async def get_by_id(self, lesson_id: UUID) -> Lesson | None: ...
    async def list_by_module(self, module_id: UUID) -> list[Lesson]: ...
    async def create(self, lesson: Lesson) -> Lesson: ...
    async def update(self, lesson: Lesson) -> Lesson: ...
    async def delete(self, lesson_id: UUID) -> None: ...
    async def reorder(self, orders: list[tuple[UUID, int]]) -> None: ...
    async def next_lesson(self, lesson: Lesson) -> Lesson | None: ...


class StudentLessonRepository(Protocol):
    async def mark_completed(self, user_id: UUID, lesson_id: UUID) -> None: ...
    async def unmark(self, user_id: UUID, lesson_id: UUID) -> None: ...
    async def completed_ids(self, user_id: UUID) -> set[UUID]: ...
```

```python
# app/domain/lessons_module/lessons_validator.py
import re
from dataclasses import dataclass

from app.domain.lessons_module.lessons_exceptions import InvalidDriveUrl

DRIVE_PATTERNS = [
    re.compile(r"/file/d/([a-zA-Z0-9_-]+)"),
    re.compile(r"[?&]id=([a-zA-Z0-9_-]+)"),
]


def parse_drive_file_id(url: str) -> str:
    for p in DRIVE_PATTERNS:
        m = p.search(url)
        if m:
            return m.group(1)
    raise InvalidDriveUrl(url)


@dataclass(frozen=True)
class DriveFileId:
    value: str
```

- [ ] **Step 4: Create comments domain files**

```python
# app/domain/comments_module/__init__.py
```

```python
# app/domain/comments_module/comments_model.py
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class Comment:
    id: UUID
    lesson_id: UUID
    user_id: UUID
    text: str
    created_at: datetime
    edited_at: datetime | None
    deleted_at: datetime | None


@dataclass
class CommentRead:
    id: UUID
    lesson_id: UUID
    user_id: UUID
    text: str | None
    created_at: datetime
    edited_at: datetime | None
    deleted_at: datetime | None
    author_name: str
    author_photo_url: str | None
```

```python
# app/domain/comments_module/comments_exceptions.py
from app.domain.shared.base_exceptions import DomainError


class CommentNotFound(DomainError):
    pass


class CommentNotOwnedByUser(DomainError):
    pass
```

```python
# app/domain/comments_module/comments_repo_interface.py
from typing import Protocol
from uuid import UUID

from app.domain.comments_module.comments_model import Comment, CommentRead


class CommentRepository(Protocol):
    async def list_by_lesson(
        self, lesson_id: UUID, page: int, page_size: int
    ) -> tuple[list[CommentRead], int]: ...
    async def get_by_id(self, comment_id: UUID) -> Comment | None: ...
    async def create(self, comment: Comment) -> Comment: ...
    async def update(self, comment: Comment) -> Comment: ...
    async def delete_comment(self, comment_id: UUID) -> None: ...
```

- [ ] **Step 5: Verify domain imports**

```bash
cd /home/sanchezz/Desktop/plataforma_atlaz_mkt_backend
python -c "
from app.domain.tracks_module.tracks_model import Track
from app.domain.tracks_module.tracks_exceptions import TrackNotFound
from app.domain.tracks_module.tracks_repo_interface import TrackRepository
from app.domain.modules_module.modules_model import Module
from app.domain.modules_module.modules_exceptions import ModuleNotFound
from app.domain.modules_module.modules_repo_interface import ModuleRepository
from app.domain.lessons_module.lessons_model import Lesson, StudentLesson
from app.domain.lessons_module.lessons_exceptions import LessonNotFound, InvalidDriveUrl
from app.domain.lessons_module.lessons_repo_interface import LessonRepository, StudentLessonRepository
from app.domain.lessons_module.lessons_validator import parse_drive_file_id
from app.domain.comments_module.comments_model import Comment, CommentRead
from app.domain.comments_module.comments_exceptions import CommentNotFound, CommentNotOwnedByUser
from app.domain.comments_module.comments_repo_interface import CommentRepository
print('domain OK')
"
```

Expected: `domain OK`

- [ ] **Step 6: Commit**

```bash
git add app/domain/tracks_module/ app/domain/modules_module/ app/domain/lessons_module/ app/domain/comments_module/
git commit -m "feat: add domain layer for tracks/modules/lessons/comments modules"
```

---

### Task 2: Database — modules_module (no cross-deps)

**Files to create:**
- `app/database/modules_module/__init__.py`
- `app/database/modules_module/modules_repo.py`

- [ ] **Step 1: Create modules_repo.py**

```python
# app/database/modules_module/__init__.py
```

```python
# app/database/modules_module/modules_repo.py
from uuid import UUID

from sqlalchemy import ForeignKey, Integer, Text, delete, select, update
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.database.shared.sqlalchemy_base import Base
from app.domain.modules_module.modules_model import Module


class ModuleModel(Base):
    __tablename__ = "modules"
    __table_args__ = {"schema": "public", "extend_existing": True}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    track_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("public.tracks.id", ondelete="CASCADE"),
        nullable=False,
    )
    titulo: Mapped[str] = mapped_column(Text, nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text, nullable=True)
    ordem: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


def _module_from_model(m: ModuleModel) -> Module:
    return Module(
        id=m.id,
        track_id=m.track_id,
        title=m.title,
        description=m.description,
        order=m.order,
    )


class SqlAlchemyModuleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_track(self, track_id: UUID) -> list[Module]:
        result = await self._session.execute(
            select(ModuleModel)
            .where(ModuleModel.track_id == track_id)
            .order_by(ModuleModel.order)
        )
        return [_module_from_model(m) for m in result.scalars()]

    async def get_by_id(self, module_id: UUID) -> Module | None:
        result = await self._session.execute(
            select(ModuleModel).where(ModuleModel.id == module_id)
        )
        m = result.scalar_one_or_none()
        return _module_from_model(m) if m else None

    async def create(self, module: Module) -> Module:
        model = ModuleModel(
            id=module.id,
            track_id=module.track_id,
            title=module.title,
            description=module.description,
            order=module.order,
        )
        self._session.add(model)
        await self._session.flush()
        return module

    async def update(self, module: Module) -> Module:
        await self._session.execute(
            update(ModuleModel)
            .where(ModuleModel.id == module.id)
            .values(
                title=module.title,
                description=module.description,
                order=module.order,
            )
        )
        return module

    async def delete(self, module_id: UUID) -> None:
        await self._session.execute(delete(ModuleModel).where(ModuleModel.id == module_id))

    async def reorder(self, orders: list[tuple[UUID, int]]) -> None:
        for module_id, order_val in orders:
            await self._session.execute(
                update(ModuleModel).where(ModuleModel.id == module_id).values(order=order_val)
            )
```

- [ ] **Step 2: Verify import**

```bash
cd /home/sanchezz/Desktop/plataforma_atlaz_mkt_backend
python -c "from app.database.modules_module.modules_repo import SqlAlchemyModuleRepository; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add app/database/modules_module/
git commit -m "feat: add database layer for modules_module"
```

---

### Task 3: Database — lessons_module (imports ModuleModel)

**Files to create:**
- `app/database/lessons_module/__init__.py`
- `app/database/lessons_module/lessons_repo.py`

- [ ] **Step 1: Create lessons_repo.py**

```python
# app/database/lessons_module/__init__.py
```

```python
# app/database/lessons_module/lessons_repo.py
from datetime import datetime
from uuid import UUID

from sqlalchemy import ForeignKey, Integer, Text, UniqueConstraint, delete, select, update
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.database.modules_module.modules_repo import ModuleModel
from app.database.shared.sqlalchemy_base import Base
from app.domain.lessons_module.lessons_model import Lesson, StudentLesson
from app.domain.shared.utils import now_sp


class LessonModel(Base):
    __tablename__ = "lessons"
    __table_args__ = {"schema": "public", "extend_existing": True}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    module_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("public.modules.id", ondelete="CASCADE"),
        nullable=False,
    )
    titulo: Mapped[str] = mapped_column(Text, nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text, nullable=True)
    drive_file_id: Mapped[str] = mapped_column(Text, nullable=False)
    duracao_minutos: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ordem: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)


class StudentLessonModel(Base):
    __tablename__ = "student_lessons"
    __table_args__ = (
        UniqueConstraint("user_id", "lesson_id"),
        {"schema": "public", "extend_existing": True},
    )

    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("public.users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    lesson_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("public.lessons.id", ondelete="CASCADE"),
        primary_key=True,
    )
    completed_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)


def _lesson_from_model(m: LessonModel) -> Lesson:
    return Lesson(
        id=m.id,
        module_id=m.module_id,
        title=m.title,
        description=m.description,
        drive_file_id=m.drive_file_id,
        duration_minutes=m.duration_minutes,
        order=m.order,
        created_at=m.created_at,
    )


class SqlAlchemyLessonRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, lesson_id: UUID) -> Lesson | None:
        result = await self._session.execute(
            select(LessonModel).where(LessonModel.id == lesson_id)
        )
        m = result.scalar_one_or_none()
        return _lesson_from_model(m) if m else None

    async def list_by_module(self, module_id: UUID) -> list[Lesson]:
        result = await self._session.execute(
            select(LessonModel)
            .where(LessonModel.module_id == module_id)
            .order_by(LessonModel.order)
        )
        return [_lesson_from_model(m) for m in result.scalars()]

    async def create(self, lesson: Lesson) -> Lesson:
        model = LessonModel(
            id=lesson.id,
            module_id=lesson.module_id,
            title=lesson.title,
            description=lesson.description,
            drive_file_id=lesson.drive_file_id,
            duration_minutes=lesson.duration_minutes,
            order=lesson.order,
            created_at=lesson.created_at,
        )
        self._session.add(model)
        await self._session.flush()
        return lesson

    async def update(self, lesson: Lesson) -> Lesson:
        await self._session.execute(
            update(LessonModel)
            .where(LessonModel.id == lesson.id)
            .values(
                title=lesson.title,
                description=lesson.description,
                drive_file_id=lesson.drive_file_id,
                duration_minutes=lesson.duration_minutes,
                order=lesson.order,
            )
        )
        return lesson

    async def delete(self, lesson_id: UUID) -> None:
        await self._session.execute(delete(LessonModel).where(LessonModel.id == lesson_id))

    async def reorder(self, orders: list[tuple[UUID, int]]) -> None:
        for lesson_id, order_val in orders:
            await self._session.execute(
                update(LessonModel).where(LessonModel.id == lesson_id).values(order=order_val)
            )

    async def next_lesson(self, lesson: Lesson) -> Lesson | None:
        result = await self._session.execute(
            select(LessonModel)
            .where(LessonModel.module_id == lesson.module_id, LessonModel.order > lesson.order)
            .order_by(LessonModel.order)
            .limit(1)
        )
        next_model = result.scalar_one_or_none()
        if next_model:
            return _lesson_from_model(next_model)

        module_result = await self._session.execute(
            select(ModuleModel).where(ModuleModel.id == lesson.module_id)
        )
        module = module_result.scalar_one_or_none()
        if module is None:
            return None

        next_module_result = await self._session.execute(
            select(ModuleModel)
            .where(
                ModuleModel.track_id == module.track_id,
                ModuleModel.order > module.order,
            )
            .order_by(ModuleModel.order)
            .limit(1)
        )
        next_module = next_module_result.scalar_one_or_none()
        if next_module is None:
            return None

        first_result = await self._session.execute(
            select(LessonModel)
            .where(LessonModel.module_id == next_module.id)
            .order_by(LessonModel.order)
            .limit(1)
        )
        first = first_result.scalar_one_or_none()
        return _lesson_from_model(first) if first else None


class SqlAlchemyStudentLessonRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def mark_completed(self, user_id: UUID, lesson_id: UUID) -> None:
        existing = await self._session.execute(
            select(StudentLessonModel).where(
                StudentLessonModel.user_id == user_id,
                StudentLessonModel.lesson_id == lesson_id,
            )
        )
        if existing.scalar_one_or_none() is None:
            self._session.add(
                StudentLessonModel(
                    user_id=user_id,
                    lesson_id=lesson_id,
                    completed_at=now_sp(),
                )
            )
            await self._session.flush()

    async def unmark(self, user_id: UUID, lesson_id: UUID) -> None:
        await self._session.execute(
            delete(StudentLessonModel).where(
                StudentLessonModel.user_id == user_id,
                StudentLessonModel.lesson_id == lesson_id,
            )
        )

    async def completed_ids(self, user_id: UUID) -> set[UUID]:
        result = await self._session.execute(
            select(StudentLessonModel.lesson_id).where(StudentLessonModel.user_id == user_id)
        )
        return set(result.scalars())
```

- [ ] **Step 2: Verify import**

```bash
cd /home/sanchezz/Desktop/plataforma_atlaz_mkt_backend
python -c "from app.database.lessons_module.lessons_repo import SqlAlchemyLessonRepository, SqlAlchemyStudentLessonRepository; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add app/database/lessons_module/
git commit -m "feat: add database layer for lessons_module"
```

---

### Task 4: Database — tracks_module and comments_module

**Files to create:**
- `app/database/tracks_module/__init__.py`
- `app/database/tracks_module/tracks_repo.py`
- `app/database/comments_module/__init__.py`
- `app/database/comments_module/comments_repo.py`

- [ ] **Step 1: Create tracks_repo.py**

```python
# app/database/tracks_module/__init__.py
```

```python
# app/database/tracks_module/tracks_repo.py
from datetime import datetime
from uuid import UUID

from sqlalchemy import Integer, Text, delete, select, update
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.database.lessons_module.lessons_repo import LessonModel
from app.database.modules_module.modules_repo import ModuleModel
from app.database.shared.sqlalchemy_base import Base
from app.domain.tracks_module.tracks_model import Track
from app.domain.shared.utils import now_sp


class TrackModel(Base):
    __tablename__ = "tracks"
    __table_args__ = {"schema": "public", "extend_existing": True}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    titulo: Mapped[str] = mapped_column(Text, nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text, nullable=True)
    capa_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    ordem: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)


def _track_from_model(m: TrackModel) -> Track:
    return Track(
        id=m.id,
        title=m.title,
        description=m.description,
        cover_url=m.cover_url,
        order=m.order,
        created_at=m.created_at,
    )


class SqlAlchemyTrackRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_all(self) -> list[Track]:
        result = await self._session.execute(
            select(TrackModel).order_by(TrackModel.order, TrackModel.created_at)
        )
        return [_track_from_model(m) for m in result.scalars()]

    async def get_by_id(self, track_id: UUID) -> Track | None:
        result = await self._session.execute(
            select(TrackModel).where(TrackModel.id == track_id)
        )
        m = result.scalar_one_or_none()
        return _track_from_model(m) if m else None

    async def create(self, track: Track) -> Track:
        model = TrackModel(
            id=track.id,
            title=track.title,
            description=track.description,
            cover_url=track.cover_url,
            order=track.order,
            created_at=track.created_at,
        )
        self._session.add(model)
        await self._session.flush()
        return track

    async def update(self, track: Track) -> Track:
        await self._session.execute(
            update(TrackModel)
            .where(TrackModel.id == track.id)
            .values(
                title=track.title,
                description=track.description,
                cover_url=track.cover_url,
                order=track.order,
            )
        )
        return track

    async def delete(self, track_id: UUID) -> None:
        await self._session.execute(delete(TrackModel).where(TrackModel.id == track_id))

    async def reorder(self, orders: list[tuple[UUID, int]]) -> None:
        for track_id, order_val in orders:
            await self._session.execute(
                update(TrackModel).where(TrackModel.id == track_id).values(order=order_val)
            )

    async def count_lessons(self, track_id: UUID) -> int:
        result = await self._session.execute(
            select(LessonModel)
            .join(ModuleModel, LessonModel.module_id == ModuleModel.id)
            .where(ModuleModel.track_id == track_id)
        )
        return len(result.scalars().all())
```

- [ ] **Step 2: Create comments_repo.py**

```python
# app/database/comments_module/__init__.py
```

```python
# app/database/comments_module/comments_repo.py
from datetime import datetime
from uuid import UUID

from sqlalchemy import ForeignKey, String, Text, select, update
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.database.shared.sqlalchemy_base import Base
from app.domain.comments_module.comments_model import Comment, CommentRead
from app.domain.shared.utils import now_sp


class CommentModel(Base):
    __tablename__ = "comments"
    __table_args__ = {"schema": "public", "extend_existing": True}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    lesson_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("public.lessons.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("public.users.id", ondelete="CASCADE"),
        nullable=False,
    )
    texto: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)
    edited_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True)


class UserContentModel(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "public", "extend_existing": True}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    photo_url: Mapped[str | None] = mapped_column(String, nullable=True)


def _comment_from_model(m: CommentModel) -> Comment:
    return Comment(
        id=m.id,
        lesson_id=m.lesson_id,
        user_id=m.user_id,
        text=m.text,
        created_at=m.created_at,
        edited_at=m.edited_at,
        deleted_at=m.deleted_at,
    )


class SqlAlchemyCommentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_lesson(
        self, lesson_id: UUID, page: int, page_size: int
    ) -> tuple[list[CommentRead], int]:
        count_result = await self._session.execute(
            select(CommentModel).where(CommentModel.lesson_id == lesson_id)
        )
        total = len(count_result.scalars().all())

        offset = (page - 1) * page_size
        result = await self._session.execute(
            select(CommentModel, UserContentModel)
            .join(UserContentModel, CommentModel.user_id == UserContentModel.id)
            .where(CommentModel.lesson_id == lesson_id)
            .order_by(CommentModel.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        rows = result.all()
        items = [
            CommentRead(
                id=c.id,
                lesson_id=c.lesson_id,
                user_id=c.user_id,
                text=None if c.deleted_at else c.text,
                created_at=c.created_at,
                edited_at=c.edited_at,
                deleted_at=c.deleted_at,
                author_name=u.name,
                author_photo_url=u.photo_url,
            )
            for c, u in rows
        ]
        return items, total

    async def get_by_id(self, comment_id: UUID) -> Comment | None:
        result = await self._session.execute(
            select(CommentModel).where(CommentModel.id == comment_id)
        )
        m = result.scalar_one_or_none()
        return _comment_from_model(m) if m else None

    async def create(self, comment: Comment) -> Comment:
        model = CommentModel(
            id=comment.id,
            lesson_id=comment.lesson_id,
            user_id=comment.user_id,
            text=comment.text,
            created_at=comment.created_at,
            edited_at=comment.edited_at,
            deleted_at=comment.deleted_at,
        )
        self._session.add(model)
        await self._session.flush()
        return comment

    async def update(self, comment: Comment) -> Comment:
        await self._session.execute(
            update(CommentModel)
            .where(CommentModel.id == comment.id)
            .values(
                text=comment.text,
                edited_at=comment.edited_at,
                deleted_at=comment.deleted_at,
            )
        )
        return comment

    async def delete_comment(self, comment_id: UUID) -> None:
        await self._session.execute(
            update(CommentModel)
            .where(CommentModel.id == comment_id)
            .values(deleted_at=now_sp())
        )
```

- [ ] **Step 3: Verify imports**

```bash
cd /home/sanchezz/Desktop/plataforma_atlaz_mkt_backend
python -c "
from app.database.tracks_module.tracks_repo import SqlAlchemyTrackRepository
from app.database.comments_module.comments_repo import SqlAlchemyCommentRepository
print('OK')
"
```

Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add app/database/tracks_module/ app/database/comments_module/
git commit -m "feat: add database layer for tracks_module and comments_module"
```

---

### Task 5: Services — all four new modules

**Files to create:**
- `app/services/tracks_module/__init__.py` + `crud_admin.py` + `get_with_modules.py` + `list_with_progress.py`
- `app/services/modules_module/__init__.py` + `crud_admin.py`
- `app/services/lessons_module/__init__.py` + `crud_admin.py` + `get.py` + `mark_completed.py` + `unmark.py`
- `app/services/comments_module/__init__.py` + `create.py` + `delete.py` + `edit.py` + `list.py`

Note: Services import DTOs from controllers (pre-existing pattern preserved). The controller DTOs don't exist yet — service files are created now but will only import-verify after Task 7 (controllers).

- [ ] **Step 1: Create tracks services**

```python
# app/services/tracks_module/__init__.py
```

```python
# app/services/tracks_module/crud_admin.py
from uuid import UUID, uuid4

from app.domain.tracks_module.tracks_exceptions import TrackNotFound
from app.domain.tracks_module.tracks_model import Track
from app.domain.tracks_module.tracks_repo_interface import TrackRepository
from app.domain.shared.utils import now_sp


class CreateTrack:
    def __init__(self, repo: TrackRepository) -> None:
        self._repo = repo

    async def execute(
        self, title: str, description: str | None, cover_url: str | None, order: int
    ) -> Track:
        track = Track(
            id=uuid4(),
            title=title,
            description=description,
            cover_url=cover_url,
            order=order,
            created_at=now_sp(),
        )
        return await self._repo.create(track)


class UpdateTrack:
    def __init__(self, repo: TrackRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        track_id: UUID,
        title: str | None,
        description: str | None,
        cover_url: str | None,
        order: int | None,
    ) -> Track:
        track = await self._repo.get_by_id(track_id)
        if track is None:
            raise TrackNotFound(f"Trilha {track_id} não encontrada.")
        updated = Track(
            id=track.id,
            title=title if title is not None else track.title,
            description=description if description is not None else track.description,
            cover_url=cover_url if cover_url is not None else track.cover_url,
            order=order if order is not None else track.order,
            created_at=track.created_at,
        )
        return await self._repo.update(updated)


class DeleteTrack:
    def __init__(self, repo: TrackRepository) -> None:
        self._repo = repo

    async def execute(self, track_id: UUID) -> None:
        track = await self._repo.get_by_id(track_id)
        if track is None:
            raise TrackNotFound(f"Trilha {track_id} não encontrada.")
        await self._repo.delete(track_id)


class ReorderTracks:
    def __init__(self, repo: TrackRepository) -> None:
        self._repo = repo

    async def execute(self, orders: list[tuple[UUID, int]]) -> None:
        await self._repo.reorder(orders)
```

```python
# app/services/tracks_module/get_with_modules.py
from uuid import UUID

from app.domain.modules_module.modules_repo_interface import ModuleRepository
from app.domain.lessons_module.lessons_repo_interface import LessonRepository, StudentLessonRepository
from app.domain.tracks_module.tracks_exceptions import TrackNotFound
from app.domain.tracks_module.tracks_repo_interface import TrackRepository


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

    async def execute(self, track_id: UUID, user_id: UUID):  # type: ignore[return]
        from app.api.controllers.tracks_module.tracks_dto.tracks_dto import (
            ModuleWithLessonsDTO,
            TrackWithModulesDTO,
        )
        from app.api.controllers.shared_content.shared_dto import LessonSummaryDTO

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
```

```python
# app/services/tracks_module/list_with_progress.py
from uuid import UUID

from app.domain.modules_module.modules_repo_interface import ModuleRepository
from app.domain.lessons_module.lessons_repo_interface import LessonRepository, StudentLessonRepository
from app.domain.tracks_module.tracks_repo_interface import TrackRepository


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

    async def execute(self, user_id: UUID):  # type: ignore[return]
        from app.api.controllers.tracks_module.tracks_dto.tracks_dto import TrackProgressDTO

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
                    total_lessons=total,
                    lessons_completed=completeds_count,
                    progress_pct=pct,
                )
            )
        return result
```

- [ ] **Step 2: Create modules services**

```python
# app/services/modules_module/__init__.py
```

```python
# app/services/modules_module/crud_admin.py
from uuid import UUID, uuid4

from app.domain.modules_module.modules_exceptions import ModuleNotFound
from app.domain.modules_module.modules_model import Module
from app.domain.modules_module.modules_repo_interface import ModuleRepository


class CreateModule:
    def __init__(self, repo: ModuleRepository) -> None:
        self._repo = repo

    async def execute(
        self, track_id: UUID, title: str, description: str | None, order: int
    ) -> Module:
        module = Module(id=uuid4(), track_id=track_id, title=title, description=description, order=order)
        return await self._repo.create(module)


class UpdateModule:
    def __init__(self, repo: ModuleRepository) -> None:
        self._repo = repo

    async def execute(
        self, module_id: UUID, title: str | None, description: str | None, order: int | None
    ) -> Module:
        module = await self._repo.get_by_id(module_id)
        if module is None:
            raise ModuleNotFound(f"Módulo {module_id} não encontrado.")
        updated = Module(
            id=module.id,
            track_id=module.track_id,
            title=title if title is not None else module.title,
            description=description if description is not None else module.description,
            order=order if order is not None else module.order,
        )
        return await self._repo.update(updated)


class DeleteModule:
    def __init__(self, repo: ModuleRepository) -> None:
        self._repo = repo

    async def execute(self, module_id: UUID) -> None:
        module = await self._repo.get_by_id(module_id)
        if module is None:
            raise ModuleNotFound(f"Módulo {module_id} não encontrado.")
        await self._repo.delete(module_id)


class ReorderModules:
    def __init__(self, repo: ModuleRepository) -> None:
        self._repo = repo

    async def execute(self, orders: list[tuple[UUID, int]]) -> None:
        await self._repo.reorder(orders)
```

- [ ] **Step 3: Create lessons services**

```python
# app/services/lessons_module/__init__.py
```

```python
# app/services/lessons_module/crud_admin.py
from uuid import UUID, uuid4

from app.domain.lessons_module.lessons_exceptions import LessonNotFound
from app.domain.lessons_module.lessons_model import Lesson
from app.domain.lessons_module.lessons_repo_interface import LessonRepository
from app.domain.lessons_module.lessons_validator import parse_drive_file_id
from app.domain.shared.utils import now_sp


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
            duration_minutes=duration_minutes if duration_minutes is not None else lesson.duration_minutes,
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
```

```python
# app/services/lessons_module/get.py
from uuid import UUID

from app.domain.lessons_module.lessons_exceptions import LessonNotFound
from app.domain.lessons_module.lessons_repo_interface import LessonRepository, StudentLessonRepository
from app.domain.modules_module.modules_exceptions import ModuleNotFound
from app.domain.modules_module.modules_repo_interface import ModuleRepository
from app.domain.tracks_module.tracks_exceptions import TrackNotFound
from app.domain.tracks_module.tracks_repo_interface import TrackRepository


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

    async def execute(self, lesson_id: UUID, user_id: UUID):  # type: ignore[return]
        from app.api.controllers.lessons_module.lessons_dto.lessons_dto import LessonDetailDTO
        from app.api.controllers.shared_content.shared_dto import LessonSummaryDTO, TrackSummaryDTO

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
```

```python
# app/services/lessons_module/mark_completed.py
from uuid import UUID

from app.domain.lessons_module.lessons_exceptions import LessonNotFound
from app.domain.lessons_module.lessons_repo_interface import LessonRepository, StudentLessonRepository


class MarkCompleted:
    def __init__(self, lesson_repo: LessonRepository, student_lesson_repo: StudentLessonRepository) -> None:
        self._lesson_repo = lesson_repo
        self._student_lesson_repo = student_lesson_repo

    async def execute(self, lesson_id: UUID, user_id: UUID) -> None:
        lesson = await self._lesson_repo.get_by_id(lesson_id)
        if lesson is None:
            raise LessonNotFound(f"Aula {lesson_id} não encontrada.")
        await self._student_lesson_repo.mark_completed(user_id, lesson_id)
```

```python
# app/services/lessons_module/unmark.py
from uuid import UUID

from app.domain.lessons_module.lessons_repo_interface import StudentLessonRepository


class Unmark:
    def __init__(self, student_lesson_repo: StudentLessonRepository) -> None:
        self._student_lesson_repo = student_lesson_repo

    async def execute(self, lesson_id: UUID, user_id: UUID) -> None:
        await self._student_lesson_repo.unmark(user_id, lesson_id)
```

- [ ] **Step 4: Create comments services**

```python
# app/services/comments_module/__init__.py
```

```python
# app/services/comments_module/create.py
from uuid import UUID, uuid4

from app.domain.comments_module.comments_model import Comment
from app.domain.comments_module.comments_repo_interface import CommentRepository
from app.domain.lessons_module.lessons_exceptions import LessonNotFound
from app.domain.lessons_module.lessons_repo_interface import LessonRepository
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
```

```python
# app/services/comments_module/delete.py
from uuid import UUID

from app.domain.comments_module.comments_exceptions import CommentNotFound, CommentNotOwnedByUser
from app.domain.comments_module.comments_repo_interface import CommentRepository


class DeleteComment:
    def __init__(self, repo: CommentRepository) -> None:
        self._repo = repo

    async def execute(self, comment_id: UUID, user_id: UUID, is_admin: bool) -> None:
        comment = await self._repo.get_by_id(comment_id)
        if comment is None:
            raise CommentNotFound(f"Comentário {comment_id} não encontrado.")
        if not is_admin and comment.user_id != user_id:
            raise CommentNotOwnedByUser("Sem permissão para apagar este comentário.")
        await self._repo.delete_comment(comment_id)
```

```python
# app/services/comments_module/edit.py
from uuid import UUID

from app.domain.comments_module.comments_exceptions import CommentNotFound, CommentNotOwnedByUser
from app.domain.comments_module.comments_model import Comment
from app.domain.comments_module.comments_repo_interface import CommentRepository
from app.domain.shared.utils import now_sp


class EditComment:
    def __init__(self, repo: CommentRepository) -> None:
        self._repo = repo

    async def execute(self, comment_id: UUID, user_id: UUID, is_admin: bool, text: str) -> Comment:
        comment = await self._repo.get_by_id(comment_id)
        if comment is None:
            raise CommentNotFound(f"Comentário {comment_id} não encontrado.")
        if not is_admin and comment.user_id != user_id:
            raise CommentNotOwnedByUser("Sem permissão para editar este comentário.")
        updated = Comment(
            id=comment.id,
            lesson_id=comment.lesson_id,
            user_id=comment.user_id,
            text=text,
            created_at=comment.created_at,
            edited_at=now_sp(),
            deleted_at=comment.deleted_at,
        )
        return await self._repo.update(updated)
```

```python
# app/services/comments_module/list.py
from uuid import UUID

from app.domain.comments_module.comments_repo_interface import CommentRepository
from app.domain.shared.dtos import PagedResponse


class ListComments:
    def __init__(self, repo: CommentRepository) -> None:
        self._repo = repo

    async def execute(self, lesson_id: UUID, page: int, page_size: int, current_user_id: UUID):  # type: ignore[return]
        from app.api.controllers.comments_module.comments_dto.comments_dto import AuthorDTO, CommentDTO

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
```

- [ ] **Step 5: Verify domain+service imports (no controller dependency yet)**

```bash
cd /home/sanchezz/Desktop/plataforma_atlaz_mkt_backend
python -c "
from app.services.tracks_module.crud_admin import CreateTrack, UpdateTrack, DeleteTrack, ReorderTracks
from app.services.modules_module.crud_admin import CreateModule, UpdateModule, DeleteModule, ReorderModules
from app.services.lessons_module.crud_admin import CreateLesson, UpdateLesson, DeleteLesson, ReorderLessons
from app.services.lessons_module.mark_completed import MarkCompleted
from app.services.lessons_module.unmark import Unmark
from app.services.comments_module.delete import DeleteComment
from app.services.comments_module.edit import EditComment
print('services OK')
"
```

Expected: `services OK`

- [ ] **Step 6: Commit**

```bash
git add app/services/tracks_module/ app/services/modules_module/ app/services/lessons_module/ app/services/comments_module/
git commit -m "feat: add services layer for tracks/modules/lessons/comments modules"
```

---

### Task 6: Controllers — shared_content + all four new modules

**Files to create:**
- `app/api/controllers/shared_content/__init__.py`
- `app/api/controllers/shared_content/shared_dto.py`
- `app/api/controllers/tracks_module/__init__.py`
- `app/api/controllers/tracks_module/tracks_dto/__init__.py`
- `app/api/controllers/tracks_module/tracks_dto/tracks_dto.py`
- `app/api/controllers/tracks_module/tracks_routes/__init__.py`
- `app/api/controllers/tracks_module/tracks_routes/tracks_router.py`
- `app/api/controllers/modules_module/__init__.py`
- `app/api/controllers/modules_module/modules_dto/__init__.py`
- `app/api/controllers/modules_module/modules_dto/modules_dto.py`
- `app/api/controllers/modules_module/modules_routes/__init__.py`
- `app/api/controllers/modules_module/modules_routes/modules_router.py`
- `app/api/controllers/lessons_module/__init__.py`
- `app/api/controllers/lessons_module/lessons_dto/__init__.py`
- `app/api/controllers/lessons_module/lessons_dto/lessons_dto.py`
- `app/api/controllers/lessons_module/lessons_routes/__init__.py`
- `app/api/controllers/lessons_module/lessons_routes/lessons_router.py`
- `app/api/controllers/comments_module/__init__.py`
- `app/api/controllers/comments_module/comments_dto/__init__.py`
- `app/api/controllers/comments_module/comments_dto/comments_dto.py`
- `app/api/controllers/comments_module/comments_routes/__init__.py`
- `app/api/controllers/comments_module/comments_routes/comments_router.py`

- [ ] **Step 1: Create shared_content/shared_dto.py**

```python
# app/api/controllers/shared_content/__init__.py
```

```python
# app/api/controllers/shared_content/shared_dto.py
from dataclasses import dataclass
from uuid import UUID

from pydantic import BaseModel, ConfigDict


@dataclass
class LessonSummaryDTO:
    id: UUID
    title: str
    duration_minutes: int | None
    order: int
    completed: bool


@dataclass
class TrackSummaryDTO:
    id: UUID
    title: str


class LessonSummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    duration_minutes: int | None
    order: int
    completed: bool


class TrackSummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str


class OrderItem(BaseModel):
    id: UUID
    order: int


class ReorderIn(BaseModel):
    order: list[OrderItem]
```

- [ ] **Step 2: Create tracks_module DTOs and router**

```python
# app/api/controllers/tracks_module/__init__.py
# app/api/controllers/tracks_module/tracks_dto/__init__.py
# app/api/controllers/tracks_module/tracks_routes/__init__.py
```

```python
# app/api/controllers/tracks_module/tracks_dto/tracks_dto.py
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.api.controllers.shared_content.shared_dto import LessonSummaryDTO, LessonSummaryOut


@dataclass
class TrackProgressDTO:
    id: UUID
    title: str
    description: str | None
    cover_url: str | None
    total_lessons: int
    lessons_completed: int
    progress_pct: float


@dataclass
class ModuleWithLessonsDTO:
    id: UUID
    title: str
    description: str | None
    order: int
    lessons: list[LessonSummaryDTO]


@dataclass
class TrackWithModulesDTO:
    id: UUID
    title: str
    description: str | None
    cover_url: str | None
    progress_pct: float
    modules: list[ModuleWithLessonsDTO]


class TrackProgressOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str | None
    cover_url: str | None
    total_lessons: int
    lessons_completed: int
    progress_pct: float


class ModuleWithLessonsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str | None
    order: int
    lessons: list[LessonSummaryOut]


class TrackWithModulesOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str | None
    cover_url: str | None
    progress_pct: float
    modules: list[ModuleWithLessonsOut]


class CreateTrackIn(BaseModel):
    title: str
    description: str | None = None
    cover_url: str | None = None
    order: int = 0


class UpdateTrackIn(BaseModel):
    title: str | None = None
    description: str | None = None
    cover_url: str | None = None
    order: int | None = None


class TrackAdminOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str | None
    cover_url: str | None
    order: int
    created_at: datetime
```

```python
# app/api/controllers/tracks_module/tracks_routes/tracks_router.py
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.api.config.dependencies.auth_deps import get_current_user, require_admin
from app.api.controllers.shared_content.shared_dto import LessonSummaryOut, ReorderIn
from app.api.controllers.tracks_module.tracks_dto.tracks_dto import (
    CreateTrackIn,
    ModuleWithLessonsOut,
    TrackAdminOut,
    TrackProgressOut,
    TrackWithModulesOut,
    UpdateTrackIn,
)
from app.database.lessons_module.lessons_repo import (
    SqlAlchemyLessonRepository,
    SqlAlchemyStudentLessonRepository,
)
from app.database.modules_module.modules_repo import SqlAlchemyModuleRepository
from app.database.shared.db_factory import get_session
from app.database.tracks_module.tracks_repo import SqlAlchemyTrackRepository
from app.domain.auth_module.auth_model import User as AuthUser
from app.domain.shared.base_exceptions import AppException
from app.domain.tracks_module.tracks_exceptions import TrackNotFound
from app.services.tracks_module.crud_admin import (
    CreateTrack,
    DeleteTrack,
    ReorderTracks,
    UpdateTrack,
)
from app.services.tracks_module.get_with_modules import GetTrackWithModules
from app.services.tracks_module.list_with_progress import ListTracksWithProgress


def _repos(session: AsyncSession):
    return (
        SqlAlchemyTrackRepository(session),
        SqlAlchemyModuleRepository(session),
        SqlAlchemyLessonRepository(session),
        SqlAlchemyStudentLessonRepository(session),
    )


def get_list_tracks(session: AsyncSession = Depends(get_session)) -> ListTracksWithProgress:
    t, m, a, aa = _repos(session)
    return ListTracksWithProgress(t, m, a, aa)


def get_track_with_modules(session: AsyncSession = Depends(get_session)) -> GetTrackWithModules:
    t, m, a, aa = _repos(session)
    return GetTrackWithModules(t, m, a, aa)


def get_create_track(session: AsyncSession = Depends(get_session)) -> CreateTrack:
    t, _, _, _ = _repos(session)
    return CreateTrack(t)


def get_update_track(session: AsyncSession = Depends(get_session)) -> UpdateTrack:
    t, _, _, _ = _repos(session)
    return UpdateTrack(t)


def get_delete_track(session: AsyncSession = Depends(get_session)) -> DeleteTrack:
    t, _, _, _ = _repos(session)
    return DeleteTrack(t)


def get_reorder_tracks(session: AsyncSession = Depends(get_session)) -> ReorderTracks:
    t, _, _, _ = _repos(session)
    return ReorderTracks(t)


router = APIRouter(tags=["content"])
admin_router = APIRouter(prefix="/admin", tags=["admin-conteudo"])


@router.get("/tracks", response_model=list[TrackProgressOut])
async def list_tracks(
    user: AuthUser = Depends(get_current_user),
    use_case: ListTracksWithProgress = Depends(get_list_tracks),
) -> list[TrackProgressOut]:
    dtos = await use_case.execute(user.id)
    return [
        TrackProgressOut(
            id=d.id,
            title=d.title,
            description=d.description,
            cover_url=d.cover_url,
            total_lessons=d.total_lessons,
            lessons_completed=d.lessons_completed,
            progress_pct=d.progress_pct,
        )
        for d in dtos
    ]


@router.get("/tracks/{track_id}", response_model=TrackWithModulesOut)
async def get_track(
    track_id: UUID,
    user: AuthUser = Depends(get_current_user),
    use_case: GetTrackWithModules = Depends(get_track_with_modules),
) -> TrackWithModulesOut:
    try:
        dto = await use_case.execute(track_id, user.id)
    except TrackNotFound as exc:
        raise AppException("TRILHA_NOT_FOUND", str(exc), 404) from exc
    return TrackWithModulesOut(
        id=dto.id,
        title=dto.title,
        description=dto.description,
        cover_url=dto.cover_url,
        progress_pct=dto.progress_pct,
        modules=[
            ModuleWithLessonsOut(
                id=m.id,
                title=m.title,
                description=m.description,
                order=m.order,
                lessons=[
                    LessonSummaryOut(
                        id=a.id,
                        title=a.title,
                        duration_minutes=a.duration_minutes,
                        order=a.order,
                        completed=a.completed,
                    )
                    for a in m.lessons
                ],
            )
            for m in dto.modules
        ],
    )


@admin_router.post("/tracks", response_model=TrackAdminOut, status_code=status.HTTP_201_CREATED)
async def create_track(
    body: CreateTrackIn,
    _: AuthUser = Depends(require_admin),
    use_case: CreateTrack = Depends(get_create_track),
) -> TrackAdminOut:
    track = await use_case.execute(body.title, body.description, body.cover_url, body.order)
    return TrackAdminOut(
        id=track.id,
        title=track.title,
        description=track.description,
        cover_url=track.cover_url,
        order=track.order,
        created_at=track.created_at,
    )


@admin_router.patch("/tracks/{track_id}", response_model=TrackAdminOut)
async def update_track(
    track_id: UUID,
    body: UpdateTrackIn,
    _: AuthUser = Depends(require_admin),
    use_case: UpdateTrack = Depends(get_update_track),
) -> TrackAdminOut:
    try:
        track = await use_case.execute(
            track_id, body.title, body.description, body.cover_url, body.order
        )
    except TrackNotFound as exc:
        raise AppException("TRILHA_NOT_FOUND", str(exc), 404) from exc
    return TrackAdminOut(
        id=track.id,
        title=track.title,
        description=track.description,
        cover_url=track.cover_url,
        order=track.order,
        created_at=track.created_at,
    )


@admin_router.delete("/tracks/{track_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_track(
    track_id: UUID,
    _: AuthUser = Depends(require_admin),
    use_case: DeleteTrack = Depends(get_delete_track),
) -> None:
    try:
        await use_case.execute(track_id)
    except TrackNotFound as exc:
        raise AppException("TRILHA_NOT_FOUND", str(exc), 404) from exc


@admin_router.post("/tracks/reorder", status_code=status.HTTP_204_NO_CONTENT)
async def reorder_tracks(
    body: ReorderIn,
    _: AuthUser = Depends(require_admin),
    use_case: ReorderTracks = Depends(get_reorder_tracks),
) -> None:
    await use_case.execute([(item.id, item.order) for item in body.order])
```

- [ ] **Step 3: Create modules_module DTOs and router**

```python
# app/api/controllers/modules_module/__init__.py
# app/api/controllers/modules_module/modules_dto/__init__.py
# app/api/controllers/modules_module/modules_routes/__init__.py
```

```python
# app/api/controllers/modules_module/modules_dto/modules_dto.py
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CreateModuleIn(BaseModel):
    track_id: UUID
    title: str
    description: str | None = None
    order: int = 0


class UpdateModuleIn(BaseModel):
    title: str | None = None
    description: str | None = None
    order: int | None = None


class ModuleAdminOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    track_id: UUID
    title: str
    description: str | None
    order: int
```

```python
# app/api/controllers/modules_module/modules_routes/modules_router.py
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.api.config.dependencies.auth_deps import require_admin
from app.api.controllers.modules_module.modules_dto.modules_dto import (
    CreateModuleIn,
    ModuleAdminOut,
    UpdateModuleIn,
)
from app.api.controllers.shared_content.shared_dto import ReorderIn
from app.database.modules_module.modules_repo import SqlAlchemyModuleRepository
from app.database.shared.db_factory import get_session
from app.domain.auth_module.auth_model import User as AuthUser
from app.domain.modules_module.modules_exceptions import ModuleNotFound
from app.domain.shared.base_exceptions import AppException
from app.services.modules_module.crud_admin import (
    CreateModule,
    DeleteModule,
    ReorderModules,
    UpdateModule,
)


def get_create_module(session: AsyncSession = Depends(get_session)) -> CreateModule:
    return CreateModule(SqlAlchemyModuleRepository(session))


def get_update_module(session: AsyncSession = Depends(get_session)) -> UpdateModule:
    return UpdateModule(SqlAlchemyModuleRepository(session))


def get_delete_module(session: AsyncSession = Depends(get_session)) -> DeleteModule:
    return DeleteModule(SqlAlchemyModuleRepository(session))


def get_reorder_modules(session: AsyncSession = Depends(get_session)) -> ReorderModules:
    return ReorderModules(SqlAlchemyModuleRepository(session))


admin_router = APIRouter(prefix="/admin", tags=["admin-conteudo"])


@admin_router.post("/modules", response_model=ModuleAdminOut, status_code=status.HTTP_201_CREATED)
async def create_module(
    body: CreateModuleIn,
    _: AuthUser = Depends(require_admin),
    use_case: CreateModule = Depends(get_create_module),
) -> ModuleAdminOut:
    module = await use_case.execute(body.track_id, body.title, body.description, body.order)
    return ModuleAdminOut(
        id=module.id, track_id=module.track_id, title=module.title,
        description=module.description, order=module.order,
    )


@admin_router.patch("/modules/{module_id}", response_model=ModuleAdminOut)
async def update_module(
    module_id: UUID,
    body: UpdateModuleIn,
    _: AuthUser = Depends(require_admin),
    use_case: UpdateModule = Depends(get_update_module),
) -> ModuleAdminOut:
    try:
        module = await use_case.execute(module_id, body.title, body.description, body.order)
    except ModuleNotFound as exc:
        raise AppException("MODULO_NOT_FOUND", str(exc), 404) from exc
    return ModuleAdminOut(
        id=module.id, track_id=module.track_id, title=module.title,
        description=module.description, order=module.order,
    )


@admin_router.delete("/modules/{module_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_module(
    module_id: UUID,
    _: AuthUser = Depends(require_admin),
    use_case: DeleteModule = Depends(get_delete_module),
) -> None:
    try:
        await use_case.execute(module_id)
    except ModuleNotFound as exc:
        raise AppException("MODULO_NOT_FOUND", str(exc), 404) from exc


@admin_router.post("/modules/reorder", status_code=status.HTTP_204_NO_CONTENT)
async def reorder_modules(
    body: ReorderIn,
    _: AuthUser = Depends(require_admin),
    use_case: ReorderModules = Depends(get_reorder_modules),
) -> None:
    await use_case.execute([(item.id, item.order) for item in body.order])
```

- [ ] **Step 4: Create lessons_module DTOs and router**

```python
# app/api/controllers/lessons_module/__init__.py
# app/api/controllers/lessons_module/lessons_dto/__init__.py
# app/api/controllers/lessons_module/lessons_routes/__init__.py
```

```python
# app/api/controllers/lessons_module/lessons_dto/lessons_dto.py
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.api.controllers.shared_content.shared_dto import (
    LessonSummaryDTO,
    LessonSummaryOut,
    TrackSummaryDTO,
    TrackSummaryOut,
)


@dataclass
class LessonDetailDTO:
    id: UUID
    module_id: UUID
    title: str
    description: str | None
    drive_file_id: str
    duration_minutes: int | None
    completed: bool
    track: TrackSummaryDTO
    next_lesson: LessonSummaryDTO | None


class LessonDetailOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    module_id: UUID
    title: str
    description: str | None
    drive_file_id: str
    duration_minutes: int | None
    completed: bool
    track: TrackSummaryOut
    next_lesson: LessonSummaryOut | None


class CreateLessonIn(BaseModel):
    module_id: UUID
    title: str
    description: str | None = None
    drive_url: str
    duration_minutes: int | None = None
    order: int = 0


class UpdateLessonIn(BaseModel):
    title: str | None = None
    description: str | None = None
    drive_url: str | None = None
    duration_minutes: int | None = None
    order: int | None = None


class LessonAdminOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    module_id: UUID
    title: str
    description: str | None
    drive_file_id: str
    duration_minutes: int | None
    order: int
    created_at: datetime
```

```python
# app/api/controllers/lessons_module/lessons_routes/lessons_router.py
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.api.config.dependencies.auth_deps import get_current_user, require_admin
from app.api.controllers.lessons_module.lessons_dto.lessons_dto import (
    CreateLessonIn,
    LessonAdminOut,
    LessonDetailOut,
    UpdateLessonIn,
)
from app.api.controllers.shared_content.shared_dto import LessonSummaryOut, ReorderIn, TrackSummaryOut
from app.database.lessons_module.lessons_repo import (
    SqlAlchemyLessonRepository,
    SqlAlchemyStudentLessonRepository,
)
from app.database.modules_module.modules_repo import SqlAlchemyModuleRepository
from app.database.shared.db_factory import get_session
from app.database.tracks_module.tracks_repo import SqlAlchemyTrackRepository
from app.domain.auth_module.auth_model import User as AuthUser
from app.domain.lessons_module.lessons_exceptions import InvalidDriveUrl, LessonNotFound
from app.domain.modules_module.modules_exceptions import ModuleNotFound
from app.domain.shared.base_exceptions import AppException
from app.domain.tracks_module.tracks_exceptions import TrackNotFound
from app.services.lessons_module.crud_admin import (
    CreateLesson,
    DeleteLesson,
    ReorderLessons,
    UpdateLesson,
)
from app.services.lessons_module.get import GetLesson
from app.services.lessons_module.mark_completed import MarkCompleted
from app.services.lessons_module.unmark import Unmark


def get_lesson(session: AsyncSession = Depends(get_session)) -> GetLesson:
    return GetLesson(
        SqlAlchemyLessonRepository(session),
        SqlAlchemyModuleRepository(session),
        SqlAlchemyTrackRepository(session),
        SqlAlchemyStudentLessonRepository(session),
    )


def get_create_lesson(session: AsyncSession = Depends(get_session)) -> CreateLesson:
    return CreateLesson(SqlAlchemyLessonRepository(session))


def get_update_lesson(session: AsyncSession = Depends(get_session)) -> UpdateLesson:
    return UpdateLesson(SqlAlchemyLessonRepository(session))


def get_delete_lesson(session: AsyncSession = Depends(get_session)) -> DeleteLesson:
    return DeleteLesson(SqlAlchemyLessonRepository(session))


def get_reorder_lessons(session: AsyncSession = Depends(get_session)) -> ReorderLessons:
    return ReorderLessons(SqlAlchemyLessonRepository(session))


def get_mark_completed(session: AsyncSession = Depends(get_session)) -> MarkCompleted:
    return MarkCompleted(
        SqlAlchemyLessonRepository(session),
        SqlAlchemyStudentLessonRepository(session),
    )


def get_unmark(session: AsyncSession = Depends(get_session)) -> Unmark:
    return Unmark(SqlAlchemyStudentLessonRepository(session))


router = APIRouter(tags=["content"])
admin_router = APIRouter(prefix="/admin", tags=["admin-conteudo"])


@router.get("/lessons/{lesson_id}", response_model=LessonDetailOut)
async def get_lesson_endpoint(
    lesson_id: UUID,
    user: AuthUser = Depends(get_current_user),
    use_case: GetLesson = Depends(get_lesson),
) -> LessonDetailOut:
    try:
        dto = await use_case.execute(lesson_id, user.id)
    except LessonNotFound as exc:
        raise AppException("AULA_NOT_FOUND", str(exc), 404) from exc
    except (ModuleNotFound, TrackNotFound) as exc:
        raise AppException("INTERNAL_ERROR", str(exc), 500) from exc
    return LessonDetailOut(
        id=dto.id,
        module_id=dto.module_id,
        title=dto.title,
        description=dto.description,
        drive_file_id=dto.drive_file_id,
        duration_minutes=dto.duration_minutes,
        completed=dto.completed,
        track=TrackSummaryOut(id=dto.track.id, title=dto.track.title),
        next_lesson=(
            LessonSummaryOut(
                id=dto.next_lesson.id,
                title=dto.next_lesson.title,
                duration_minutes=dto.next_lesson.duration_minutes,
                order=dto.next_lesson.order,
                completed=dto.next_lesson.completed,
            )
            if dto.next_lesson
            else None
        ),
    )


@router.post("/lessons/{lesson_id}/complete", status_code=status.HTTP_204_NO_CONTENT)
async def mark_lesson_completed(
    lesson_id: UUID,
    user: AuthUser = Depends(get_current_user),
    use_case: MarkCompleted = Depends(get_mark_completed),
) -> None:
    try:
        await use_case.execute(lesson_id, user.id)
    except LessonNotFound as exc:
        raise AppException("AULA_NOT_FOUND", str(exc), 404) from exc


@router.delete("/lessons/{lesson_id}/complete", status_code=status.HTTP_204_NO_CONTENT)
async def unmark_lesson_completed(
    lesson_id: UUID,
    user: AuthUser = Depends(get_current_user),
    use_case: Unmark = Depends(get_unmark),
) -> None:
    await use_case.execute(lesson_id, user.id)


@admin_router.post("/lessons", response_model=LessonAdminOut, status_code=status.HTTP_201_CREATED)
async def create_lesson(
    body: CreateLessonIn,
    _: AuthUser = Depends(require_admin),
    use_case: CreateLesson = Depends(get_create_lesson),
) -> LessonAdminOut:
    try:
        lesson = await use_case.execute(
            body.module_id, body.title, body.description,
            body.drive_url, body.duration_minutes, body.order,
        )
    except InvalidDriveUrl as exc:
        raise AppException("DRIVE_URL_INVALID", str(exc), 400) from exc
    return LessonAdminOut(
        id=lesson.id, module_id=lesson.module_id, title=lesson.title,
        description=lesson.description, drive_file_id=lesson.drive_file_id,
        duration_minutes=lesson.duration_minutes, order=lesson.order, created_at=lesson.created_at,
    )


@admin_router.patch("/lessons/{lesson_id}", response_model=LessonAdminOut)
async def update_lesson(
    lesson_id: UUID,
    body: UpdateLessonIn,
    _: AuthUser = Depends(require_admin),
    use_case: UpdateLesson = Depends(get_update_lesson),
) -> LessonAdminOut:
    try:
        lesson = await use_case.execute(
            lesson_id, body.title, body.description,
            body.drive_url, body.duration_minutes, body.order,
        )
    except LessonNotFound as exc:
        raise AppException("AULA_NOT_FOUND", str(exc), 404) from exc
    except InvalidDriveUrl as exc:
        raise AppException("DRIVE_URL_INVALID", str(exc), 400) from exc
    return LessonAdminOut(
        id=lesson.id, module_id=lesson.module_id, title=lesson.title,
        description=lesson.description, drive_file_id=lesson.drive_file_id,
        duration_minutes=lesson.duration_minutes, order=lesson.order, created_at=lesson.created_at,
    )


@admin_router.delete("/lessons/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lesson(
    lesson_id: UUID,
    _: AuthUser = Depends(require_admin),
    use_case: DeleteLesson = Depends(get_delete_lesson),
) -> None:
    try:
        await use_case.execute(lesson_id)
    except LessonNotFound as exc:
        raise AppException("AULA_NOT_FOUND", str(exc), 404) from exc


@admin_router.post("/lessons/reorder", status_code=status.HTTP_204_NO_CONTENT)
async def reorder_lessons(
    body: ReorderIn,
    _: AuthUser = Depends(require_admin),
    use_case: ReorderLessons = Depends(get_reorder_lessons),
) -> None:
    await use_case.execute([(item.id, item.order) for item in body.order])
```

- [ ] **Step 5: Create comments_module DTOs and router**

```python
# app/api/controllers/comments_module/__init__.py
# app/api/controllers/comments_module/comments_dto/__init__.py
# app/api/controllers/comments_module/comments_routes/__init__.py
```

```python
# app/api/controllers/comments_module/comments_dto/comments_dto.py
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


@dataclass
class AuthorDTO:
    id: UUID
    name: str
    photo_url: str | None


@dataclass
class CommentDTO:
    id: UUID
    author: AuthorDTO
    text: str | None
    created_at: datetime
    edited_at: datetime | None
    deleted_at: datetime | None
    is_own: bool


class AuthorOut(BaseModel):
    id: UUID
    name: str
    photo_url: str | None


class CommentOut(BaseModel):
    id: UUID
    author: AuthorOut
    text: str | None
    created_at: datetime
    edited_at: datetime | None
    deleted_at: datetime | None
    is_own: bool


class CreateCommentIn(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)


class EditCommentIn(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)
```

```python
# app/api/controllers/comments_module/comments_routes/comments_router.py
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.api.config.dependencies.auth_deps import get_current_user
from app.api.controllers.comments_module.comments_dto.comments_dto import (
    AuthorOut,
    CommentOut,
    CreateCommentIn,
    EditCommentIn,
)
from app.database.comments_module.comments_repo import SqlAlchemyCommentRepository
from app.database.lessons_module.lessons_repo import SqlAlchemyLessonRepository
from app.database.shared.db_factory import get_session
from app.domain.auth_module.auth_model import User as AuthUser
from app.domain.comments_module.comments_exceptions import CommentNotFound, CommentNotOwnedByUser
from app.domain.lessons_module.lessons_exceptions import LessonNotFound
from app.domain.shared.base_exceptions import AppException
from app.domain.shared.dtos import PagedResponse
from app.services.comments_module.create import CreateComment
from app.services.comments_module.delete import DeleteComment
from app.services.comments_module.edit import EditComment
from app.services.comments_module.list import ListComments


def get_list_comments(session: AsyncSession = Depends(get_session)) -> ListComments:
    return ListComments(SqlAlchemyCommentRepository(session))


def get_create_comment(session: AsyncSession = Depends(get_session)) -> CreateComment:
    return CreateComment(
        SqlAlchemyLessonRepository(session),
        SqlAlchemyCommentRepository(session),
    )


def get_edit_comment(session: AsyncSession = Depends(get_session)) -> EditComment:
    return EditComment(SqlAlchemyCommentRepository(session))


def get_delete_comment(session: AsyncSession = Depends(get_session)) -> DeleteComment:
    return DeleteComment(SqlAlchemyCommentRepository(session))


router = APIRouter(tags=["comments"])


@router.get("/lessons/{lesson_id}/comments", response_model=PagedResponse[CommentOut])
async def list_comments(
    lesson_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: AuthUser = Depends(get_current_user),
    use_case: ListComments = Depends(get_list_comments),
) -> PagedResponse[CommentOut]:
    result = await use_case.execute(lesson_id, page, page_size, user.id)
    return PagedResponse(
        items=[
            CommentOut(
                id=c.id,
                author=AuthorOut(id=c.author.id, name=c.author.name, photo_url=c.author.photo_url),
                text=c.text,
                created_at=c.created_at,
                edited_at=c.edited_at,
                deleted_at=c.deleted_at,
                is_own=c.is_own,
            )
            for c in result.items
        ],
        page=result.page,
        page_size=result.page_size,
        total=result.total,
    )


@router.post(
    "/lessons/{lesson_id}/comments",
    response_model=CommentOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_comment(
    lesson_id: UUID,
    body: CreateCommentIn,
    user: AuthUser = Depends(get_current_user),
    use_case: CreateComment = Depends(get_create_comment),
) -> CommentOut:
    try:
        comment = await use_case.execute(lesson_id, user.id, body.text)
    except LessonNotFound as exc:
        raise AppException("AULA_NOT_FOUND", str(exc), 404) from exc
    return CommentOut(
        id=comment.id,
        author=AuthorOut(id=user.id, name="", photo_url=None),
        text=comment.text,
        created_at=comment.created_at,
        edited_at=comment.edited_at,
        deleted_at=comment.deleted_at,
        is_own=True,
    )


@router.patch("/comments/{comment_id}", response_model=CommentOut)
async def edit_comment(
    comment_id: UUID,
    body: EditCommentIn,
    user: AuthUser = Depends(get_current_user),
    use_case: EditComment = Depends(get_edit_comment),
) -> CommentOut:
    try:
        comment = await use_case.execute(comment_id, user.id, user.role == "admin", body.text)
    except CommentNotFound as exc:
        raise AppException("COMENTARIO_NOT_FOUND", str(exc), 404) from exc
    except CommentNotOwnedByUser as exc:
        raise AppException("FORBIDDEN", str(exc), 403) from exc
    return CommentOut(
        id=comment.id,
        author=AuthorOut(id=user.id, name="", photo_url=None),
        text=comment.text,
        created_at=comment.created_at,
        edited_at=comment.edited_at,
        deleted_at=comment.deleted_at,
        is_own=True,
    )


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: UUID,
    user: AuthUser = Depends(get_current_user),
    use_case: DeleteComment = Depends(get_delete_comment),
) -> None:
    try:
        await use_case.execute(comment_id, user.id, user.role == "admin")
    except CommentNotFound as exc:
        raise AppException("COMENTARIO_NOT_FOUND", str(exc), 404) from exc
    except CommentNotOwnedByUser as exc:
        raise AppException("FORBIDDEN", str(exc), 403) from exc
```

- [ ] **Step 6: Verify all controller imports**

```bash
cd /home/sanchezz/Desktop/plataforma_atlaz_mkt_backend
python -c "
from app.api.controllers.shared_content.shared_dto import LessonSummaryDTO, TrackSummaryDTO, ReorderIn
from app.api.controllers.tracks_module.tracks_routes.tracks_router import router, admin_router
from app.api.controllers.modules_module.modules_routes.modules_router import admin_router as modules_admin
from app.api.controllers.lessons_module.lessons_routes.lessons_router import router as lessons_router
from app.api.controllers.comments_module.comments_routes.comments_router import router as comments_router
print('controllers OK')
"
```

Expected: `controllers OK`

- [ ] **Step 7: Verify services that defer controller imports now work**

```bash
cd /home/sanchezz/Desktop/plataforma_atlaz_mkt_backend
python -c "
from app.services.tracks_module.get_with_modules import GetTrackWithModules
from app.services.tracks_module.list_with_progress import ListTracksWithProgress
from app.services.lessons_module.get import GetLesson
from app.services.comments_module.list import ListComments
print('deferred imports OK')
"
```

Expected: `deferred imports OK`

- [ ] **Step 8: Commit**

```bash
git add app/api/controllers/shared_content/ app/api/controllers/tracks_module/ app/api/controllers/modules_module/ app/api/controllers/lessons_module/ app/api/controllers/comments_module/
git commit -m "feat: add controller layer (DTOs + routers) for tracks/modules/lessons/comments modules"
```

---

### Task 7: Wire main.py and migrations

**Files to modify:**
- `app/main.py`
- `app/database/migrations/env.py`

- [ ] **Step 1: Update main.py**

Replace the entire router import block and router registration section. The new `app/main.py` router section (replace lines 20–35 and 143–151 of the original):

```python
# Replace these imports in app/main.py:
from app.api.controllers.auth_module.auth_routes.auth_router import router as auth_router
from app.api.controllers.comments_module.comments_routes.comments_router import (
    router as comments_router,
)
from app.api.controllers.community_module.community_routes.community_router import (
    router as community_router,
)
from app.api.controllers.lessons_module.lessons_routes.lessons_router import (
    admin_router as admin_lessons_router,
    router as lessons_router,
)
from app.api.controllers.metrics_module.metrics_routes.metrics_router import (
    admin_router as admin_metrics_router,
)
from app.api.controllers.metrics_module.metrics_routes.metrics_router import (
    router as metrics_router,
)
from app.api.controllers.modules_module.modules_routes.modules_router import (
    admin_router as admin_modules_router,
)
from app.api.controllers.tracks_module.tracks_routes.tracks_router import (
    admin_router as admin_tracks_router,
    router as tracks_router,
)
from app.api.controllers.user_module.user_routes.user_router import router as users_router
```

```python
# Replace router registrations at the bottom of app/main.py:
app.include_router(auth_router, prefix="/api/v1")
app.include_router(community_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(tracks_router, prefix="/api/v1")
app.include_router(admin_tracks_router, prefix="/api/v1")
app.include_router(admin_modules_router, prefix="/api/v1")
app.include_router(lessons_router, prefix="/api/v1")
app.include_router(admin_lessons_router, prefix="/api/v1")
app.include_router(comments_router, prefix="/api/v1")
app.include_router(metrics_router, prefix="/api/v1")
app.include_router(admin_metrics_router, prefix="/api/v1")
```

- [ ] **Step 2: Update migrations/env.py**

Replace line 22 (`import app.database.content_module.content_repo`) with four imports:

```python
import app.database.tracks_module.tracks_repo  # noqa: F401
import app.database.modules_module.modules_repo  # noqa: F401
import app.database.lessons_module.lessons_repo  # noqa: F401
import app.database.comments_module.comments_repo  # noqa: F401
```

- [ ] **Step 3: Verify app loads**

```bash
cd /home/sanchezz/Desktop/plataforma_atlaz_mkt_backend
python -c "from app.main import app; print('app OK')"
```

Expected: `app OK`

- [ ] **Step 4: Commit**

```bash
git add app/main.py app/database/migrations/env.py
git commit -m "feat: wire new module routers into main.py and update alembic model imports"
```

---

### Task 8: Update tests

**Files to modify:**
- `tests/unit/content/test_tracks_use_cases.py`
- `tests/unit/content/test_modules_use_cases.py`
- `tests/unit/content/test_lessons_use_cases.py`
- `tests/unit/content/test_comments_use_cases.py`
- `tests/unit/content/test_get_track_and_lesson.py`
- `tests/unit/content/test_rules.py`
- `tests/unit/content/test_routers.py`

- [ ] **Step 1: Update test_tracks_use_cases.py imports**

Replace the import block (lines 6–14):

```python
from app.domain.tracks_module.tracks_exceptions import TrackNotFound
from app.domain.tracks_module.tracks_model import Track
from app.domain.modules_module.modules_model import Module
from app.domain.lessons_module.lessons_model import Lesson
from app.services.tracks_module.crud_admin import (
    CreateTrack,
    DeleteTrack,
    ReorderTracks,
    UpdateTrack,
)
from app.services.tracks_module.list_with_progress import ListTracksWithProgress
```

- [ ] **Step 2: Update test_modules_use_cases.py imports**

Replace the import block (lines 5–11):

```python
from app.domain.modules_module.modules_exceptions import ModuleNotFound
from app.domain.modules_module.modules_model import Module
from app.services.modules_module.crud_admin import (
    CreateModule,
    DeleteModule,
    ReorderModules,
    UpdateModule,
)
```

- [ ] **Step 3: Update test_lessons_use_cases.py imports**

Replace the import block (lines 6–14):

```python
from app.domain.lessons_module.lessons_exceptions import InvalidDriveUrl, LessonNotFound
from app.domain.lessons_module.lessons_model import Lesson
from app.services.lessons_module.crud_admin import (
    CreateLesson,
    DeleteLesson,
    ReorderLessons,
    UpdateLesson,
)
from app.services.lessons_module.mark_completed import MarkCompleted
from app.services.lessons_module.unmark import Unmark
```

- [ ] **Step 4: Update test_comments_use_cases.py imports**

Replace the import block (lines 6–16):

```python
from app.domain.comments_module.comments_exceptions import CommentNotFound, CommentNotOwnedByUser
from app.domain.comments_module.comments_model import Comment, CommentRead
from app.domain.lessons_module.lessons_exceptions import LessonNotFound
from app.domain.lessons_module.lessons_model import Lesson
from app.services.comments_module.create import CreateComment
from app.services.comments_module.delete import DeleteComment
from app.services.comments_module.edit import EditComment
from app.services.comments_module.list import ListComments
```

- [ ] **Step 5: Update test_get_track_and_lesson.py imports**

Replace the import block (lines 6–10):

```python
from app.domain.lessons_module.lessons_exceptions import LessonNotFound
from app.domain.lessons_module.lessons_model import Lesson
from app.domain.modules_module.modules_model import Module
from app.domain.tracks_module.tracks_exceptions import TrackNotFound
from app.domain.tracks_module.tracks_model import Track
from app.services.lessons_module.get import GetLesson
from app.services.tracks_module.get_with_modules import GetTrackWithModules
```

- [ ] **Step 6: Update test_rules.py imports**

Replace the import block (lines 3–4):

```python
from app.domain.lessons_module.lessons_exceptions import InvalidDriveUrl
from app.domain.lessons_module.lessons_validator import parse_drive_file_id
```

- [ ] **Step 7: Update test_routers.py imports**

Replace the import block (lines 10–50):

```python
from app.api.config.dependencies.auth_deps import get_current_user, require_admin
from app.api.controllers.comments_module.comments_dto.comments_dto import (
    AuthorDTO,
    CommentDTO,
)
from app.api.controllers.comments_module.comments_routes.comments_router import (
    get_delete_comment,
    get_edit_comment,
    get_list_comments,
)
from app.api.controllers.lessons_module.lessons_dto.lessons_dto import LessonDetailDTO
from app.api.controllers.lessons_module.lessons_routes.lessons_router import (
    get_create_lesson,
    get_delete_lesson,
    get_lesson,
    get_mark_completed,
    get_reorder_lessons,
    get_unmark,
)
from app.api.controllers.modules_module.modules_routes.modules_router import (
    get_create_module,
    get_delete_module,
    get_reorder_modules,
    get_update_module,
)
from app.api.controllers.shared_content.shared_dto import TrackSummaryDTO
from app.api.controllers.tracks_module.tracks_dto.tracks_dto import (
    ModuleWithLessonsDTO,
    TrackProgressDTO,
    TrackWithModulesDTO,
)
from app.api.controllers.tracks_module.tracks_routes.tracks_router import (
    get_create_track,
    get_delete_track,
    get_list_tracks,
    get_reorder_tracks,
    get_track_with_modules,
    get_update_track,
)
from app.domain.auth_module.auth_model import User
from app.domain.comments_module.comments_exceptions import CommentNotFound, CommentNotOwnedByUser
from app.domain.lessons_module.lessons_exceptions import InvalidDriveUrl, LessonNotFound
from app.domain.modules_module.modules_exceptions import ModuleNotFound
from app.domain.tracks_module.tracks_exceptions import TrackNotFound
from app.domain.lessons_module.lessons_model import Lesson
from app.domain.modules_module.modules_model import Module
from app.domain.tracks_module.tracks_model import Track
from app.domain.shared.dtos import PagedResponse
from app.main import app
```

- [ ] **Step 8: Run unit tests**

```bash
cd /home/sanchezz/Desktop/plataforma_atlaz_mkt_backend
python -m pytest tests/unit/content/ -v
```

Expected: all tests pass (no failures, no import errors).

- [ ] **Step 9: Commit**

```bash
git add tests/unit/content/
git commit -m "refactor: update content unit test imports to new module paths"
```

---

### Task 9: Delete old content_module and final verification

- [ ] **Step 1: Delete old content_module directories**

```bash
rm -rf /home/sanchezz/Desktop/plataforma_atlaz_mkt_backend/app/api/controllers/content_module
rm -rf /home/sanchezz/Desktop/plataforma_atlaz_mkt_backend/app/services/content_module
rm -rf /home/sanchezz/Desktop/plataforma_atlaz_mkt_backend/app/domain/content_module
rm -rf /home/sanchezz/Desktop/plataforma_atlaz_mkt_backend/app/database/content_module
```

- [ ] **Step 2: Verify app still loads**

```bash
cd /home/sanchezz/Desktop/plataforma_atlaz_mkt_backend
python -c "from app.main import app; print('app OK')"
```

Expected: `app OK`

- [ ] **Step 3: Run full unit test suite**

```bash
cd /home/sanchezz/Desktop/plataforma_atlaz_mkt_backend
python -m pytest tests/unit/ -v
```

Expected: all tests pass.

- [ ] **Step 4: Final commit**

```bash
git add -A
git commit -m "refactor: delete old content_module — split complete into tracks/modules/lessons/comments"
```
