from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from app.contexts.content.application.use_cases.lessons.crud_admin import (
    UpdateLesson,
    CreateLesson,
    DeleteLesson,
)
from app.contexts.content.application.use_cases.lessons.unmark import Unmark
from app.contexts.content.application.use_cases.lessons.mark_completed import MarkCompleted
from app.contexts.content.domain.entities import Lesson
from app.contexts.content.domain.exceptions import LessonNotFound, InvalidDriveUrl


# ── Fake repos ─────────────────────────────────────────────────────────────────

class FakeAulaRepo:
    def __init__(self, aulas: list[Lesson] | None = None) -> None:
        self._aulas: list[Lesson] = aulas or []

    async def get_by_id(self, aula_id: UUID) -> Lesson | None:
        return next((a for a in self._aulas if a.id == aula_id), None)

    async def create(self, aula: Lesson) -> Lesson:
        self._aulas.append(aula)
        return aula

    async def update(self, aula: Lesson) -> Lesson:
        self._aulas = [aula if a.id == aula.id else a for a in self._aulas]
        return aula

    async def delete(self, aula_id: UUID) -> None:
        self._aulas = [a for a in self._aulas if a.id != aula_id]


class FakeAlunoAulaRepo:
    def __init__(self) -> None:
        self._concluidas: set[tuple[UUID, UUID]] = set()

    async def mark_completed(self, usuario_id: UUID, aula_id: UUID) -> None:
        self._concluidas.add((usuario_id, aula_id))

    async def unmark(self, usuario_id: UUID, aula_id: UUID) -> None:
        self._concluidas.discard((usuario_id, aula_id))

    async def completed_ids(self, usuario_id: UUID) -> set[UUID]:
        return {aula_id for uid, aula_id in self._concluidas if uid == usuario_id}


def _make_aula(drive_file_id: str = "abc123") -> Lesson:
    return Lesson(
        id=uuid4(),
        modulo_id=uuid4(),
        titulo="Aula",
        descricao=None,
        drive_file_id=drive_file_id,
        duracao_minutos=None,
        ordem=0,
        criado_em=datetime.now(tz=UTC),
    )


# ── CreateLesson ──────────────────────────────────────────────────────────────────

async def test_criar_aula_extracts_drive_id() -> None:
    repo = FakeAulaRepo()
    use_case = CreateLesson(repo)
    aula = await use_case.execute(
        uuid4(), "Título", None, "https://drive.google.com/file/d/abc123/view", None, 0
    )
    assert aula.drive_file_id == "abc123"


async def test_criar_aula_invalid_drive_url_raises() -> None:
    repo = FakeAulaRepo()
    use_case = CreateLesson(repo)
    with pytest.raises(InvalidDriveUrl):
        await use_case.execute(uuid4(), "T", None, "https://example.com/bad", None, 0)


# ── UpdateLesson ──────────────────────────────────────────────────────────────

async def test_atualizar_aula_not_found_raises() -> None:
    repo = FakeAulaRepo()
    use_case = UpdateLesson(repo)
    with pytest.raises(LessonNotFound):
        await use_case.execute(uuid4(), None, None, None, None, None)


async def test_atualizar_aula_updates_drive_url() -> None:
    aula = _make_aula()
    repo = FakeAulaRepo([aula])
    use_case = UpdateLesson(repo)
    updated = await use_case.execute(
        aula.id, None, None, "https://drive.google.com/file/d/newid/view", None, None
    )
    assert updated.drive_file_id == "newid"


# ── DeleteLesson ────────────────────────────────────────────────────────────────

async def test_remover_aula_not_found_raises() -> None:
    use_case = DeleteLesson(FakeAulaRepo())
    with pytest.raises(LessonNotFound):
        await use_case.execute(uuid4())


# ── MarkCompleted / Desmarcar ────────────────────────────────────────────────

async def test_marcar_concluida_idempotente() -> None:
    aula = _make_aula()
    aula_repo = FakeAulaRepo([aula])
    aluno_repo = FakeAlunoAulaRepo()
    use_case = MarkCompleted(aula_repo, aluno_repo)
    usuario_id = uuid4()
    await use_case.execute(aula.id, usuario_id)
    await use_case.execute(aula.id, usuario_id)
    assert len(aluno_repo._concluidas) == 1


async def test_marcar_concluida_aula_not_found_raises() -> None:
    use_case = MarkCompleted(FakeAulaRepo(), FakeAlunoAulaRepo())
    with pytest.raises(LessonNotFound):
        await use_case.execute(uuid4(), uuid4())


async def test_desmarcar_concluida_idempotente() -> None:
    aluno_repo = FakeAlunoAulaRepo()
    use_case = Unmark(aluno_repo)
    usuario_id = uuid4()
    aula_id = uuid4()
    # Desmarcar sem ter marcado não deve falhar
    await use_case.execute(aula_id, usuario_id)
    assert len(aluno_repo._concluidas) == 0
