from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from app.contexts.conteudo.application.use_cases.aulas.crud_admin import (
    AtualizarAula,
    CriarAula,
    RemoverAula,
)
from app.contexts.conteudo.application.use_cases.aulas.desmarcar import DesmarcarConcluida
from app.contexts.conteudo.application.use_cases.aulas.marcar_concluida import MarcarConcluida
from app.contexts.conteudo.domain.entities import Aula
from app.contexts.conteudo.domain.exceptions import AulaNaoEncontrada, DriveUrlInvalida


# ── Fake repos ─────────────────────────────────────────────────────────────────

class FakeAulaRepo:
    def __init__(self, aulas: list[Aula] | None = None) -> None:
        self._aulas: list[Aula] = aulas or []

    async def por_id(self, aula_id: UUID) -> Aula | None:
        return next((a for a in self._aulas if a.id == aula_id), None)

    async def criar(self, aula: Aula) -> Aula:
        self._aulas.append(aula)
        return aula

    async def atualizar(self, aula: Aula) -> Aula:
        self._aulas = [aula if a.id == aula.id else a for a in self._aulas]
        return aula

    async def remover(self, aula_id: UUID) -> None:
        self._aulas = [a for a in self._aulas if a.id != aula_id]


class FakeAlunoAulaRepo:
    def __init__(self) -> None:
        self._concluidas: set[tuple[UUID, UUID]] = set()

    async def marcar_concluida(self, usuario_id: UUID, aula_id: UUID) -> None:
        self._concluidas.add((usuario_id, aula_id))

    async def desmarcar(self, usuario_id: UUID, aula_id: UUID) -> None:
        self._concluidas.discard((usuario_id, aula_id))

    async def concluidas_ids(self, usuario_id: UUID) -> set[UUID]:
        return {aula_id for uid, aula_id in self._concluidas if uid == usuario_id}


def _make_aula(drive_file_id: str = "abc123") -> Aula:
    return Aula(
        id=uuid4(),
        modulo_id=uuid4(),
        titulo="Aula",
        descricao=None,
        drive_file_id=drive_file_id,
        duracao_minutos=None,
        ordem=0,
        criado_em=datetime.now(tz=UTC),
    )


# ── CriarAula ──────────────────────────────────────────────────────────────────

async def test_criar_aula_extracts_drive_id() -> None:
    repo = FakeAulaRepo()
    use_case = CriarAula(repo)
    aula = await use_case.execute(
        uuid4(), "Título", None, "https://drive.google.com/file/d/abc123/view", None, 0
    )
    assert aula.drive_file_id == "abc123"


async def test_criar_aula_invalid_drive_url_raises() -> None:
    repo = FakeAulaRepo()
    use_case = CriarAula(repo)
    with pytest.raises(DriveUrlInvalida):
        await use_case.execute(uuid4(), "T", None, "https://example.com/bad", None, 0)


# ── AtualizarAula ──────────────────────────────────────────────────────────────

async def test_atualizar_aula_not_found_raises() -> None:
    repo = FakeAulaRepo()
    use_case = AtualizarAula(repo)
    with pytest.raises(AulaNaoEncontrada):
        await use_case.execute(uuid4(), None, None, None, None, None)


async def test_atualizar_aula_updates_drive_url() -> None:
    aula = _make_aula()
    repo = FakeAulaRepo([aula])
    use_case = AtualizarAula(repo)
    updated = await use_case.execute(
        aula.id, None, None, "https://drive.google.com/file/d/newid/view", None, None
    )
    assert updated.drive_file_id == "newid"


# ── RemoverAula ────────────────────────────────────────────────────────────────

async def test_remover_aula_not_found_raises() -> None:
    use_case = RemoverAula(FakeAulaRepo())
    with pytest.raises(AulaNaoEncontrada):
        await use_case.execute(uuid4())


# ── MarcarConcluida / Desmarcar ────────────────────────────────────────────────

async def test_marcar_concluida_idempotente() -> None:
    aula = _make_aula()
    aula_repo = FakeAulaRepo([aula])
    aluno_repo = FakeAlunoAulaRepo()
    use_case = MarcarConcluida(aula_repo, aluno_repo)
    usuario_id = uuid4()
    await use_case.execute(aula.id, usuario_id)
    await use_case.execute(aula.id, usuario_id)
    assert len(aluno_repo._concluidas) == 1


async def test_marcar_concluida_aula_not_found_raises() -> None:
    use_case = MarcarConcluida(FakeAulaRepo(), FakeAlunoAulaRepo())
    with pytest.raises(AulaNaoEncontrada):
        await use_case.execute(uuid4(), uuid4())


async def test_desmarcar_concluida_idempotente() -> None:
    aluno_repo = FakeAlunoAulaRepo()
    use_case = DesmarcarConcluida(aluno_repo)
    usuario_id = uuid4()
    aula_id = uuid4()
    # Desmarcar sem ter marcado não deve falhar
    await use_case.execute(aula_id, usuario_id)
    assert len(aluno_repo._concluidas) == 0
