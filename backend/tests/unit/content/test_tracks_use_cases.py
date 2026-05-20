from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from app.contexts.content.application.use_cases.tracks.crud_admin import (
    UpdateTrack,
    CreateTrack,
    DeleteTrack,
    ReorderTracks,
)
from app.contexts.content.application.use_cases.tracks.list_with_progress import (
    ListTracksWithProgress,
)
from app.contexts.content.domain.entities import Aula, Modulo, Trilha
from app.contexts.content.domain.exceptions import TrackNotFound


# ── Fake repos ─────────────────────────────────────────────────────────────────

class FakeTrilhaRepo:
    def __init__(self, trilhas: list[Track] | None = None) -> None:
        self._trilhas: list[Track] = trilhas or []
        self.reorder_calls: list[list[tuple[UUID, int]]] = []

    async def list_all(self) -> list[Track]:
        return list(self._trilhas)

    async def get_by_id(self, trilha_id: UUID) -> Track | None:
        return next((t for t in self._trilhas if t.id == trilha_id), None)

    async def create(self, trilha: Track) -> Track:
        self._trilhas.append(trilha)
        return trilha

    async def update(self, trilha: Track) -> Track:
        self._trilhas = [trilha if t.id == trilha.id else t for t in self._trilhas]
        return trilha

    async def delete(self, trilha_id: UUID) -> None:
        self._trilhas = [t for t in self._trilhas if t.id != trilha_id]

    async def reorder(self, ordens: list[tuple[UUID, int]]) -> None:
        self.reorder_calls.append(ordens)

    async def count_lessons(self, trilha_id: UUID) -> int:
        return 0


class FakeModuloRepo:
    def __init__(self, modulos: list[Module] | None = None) -> None:
        self._modulos = modulos or []

    async def list_by_track(self, trilha_id: UUID) -> list[Module]:
        return [m for m in self._modulos if m.trilha_id == trilha_id]


class FakeAulaRepo:
    def __init__(self, aulas: list[Lesson] | None = None) -> None:
        self._aulas = aulas or []

    async def list_by_module(self, modulo_id: UUID) -> list[Lesson]:
        return [a for a in self._aulas if a.modulo_id == modulo_id]


class FakeAlunoAulaRepo:
    def __init__(self, concluidas: set[UUID] | None = None) -> None:
        self._concluidas: set[UUID] = concluidas or set()

    async def completed_ids(self, usuario_id: UUID) -> set[UUID]:
        return self._concluidas


# ── CreateTrack ────────────────────────────────────────────────────────────────

async def test_criar_trilha_returns_trilha() -> None:
    repo = FakeTrilhaRepo()
    use_case = CreateTrack(repo)
    trilha = await use_case.execute("Prospecção", "desc", None, 0)
    assert trilha.titulo == "Prospecção"
    assert trilha.ordem == 0
    assert len(repo._trilhas) == 1


async def test_criar_trilha_generates_uuid() -> None:
    repo = FakeTrilhaRepo()
    use_case = CreateTrack(repo)
    t1 = await use_case.execute("T1", None, None, 0)
    t2 = await use_case.execute("T2", None, None, 0)
    assert t1.id != t2.id


# ── UpdateTrack ────────────────────────────────────────────────────────────

def _make_trilha(titulo: str = "Trilha", ordem: int = 0) -> Track:
    return Track(
        id=uuid4(),
        titulo=titulo,
        descricao=None,
        capa_url=None,
        ordem=ordem,
        criado_em=datetime.now(tz=UTC),
    )


async def test_atualizar_trilha_changes_titulo() -> None:
    trilha = _make_trilha("Antiga")
    repo = FakeTrilhaRepo([trilha])
    use_case = UpdateTrack(repo)
    updated = await use_case.execute(trilha.id, "Nova", None, None, None)
    assert updated.titulo == "Nova"


async def test_atualizar_trilha_not_found_raises() -> None:
    repo = FakeTrilhaRepo()
    use_case = UpdateTrack(repo)
    with pytest.raises(TrackNotFound):
        await use_case.execute(uuid4(), "X", None, None, None)


async def test_atualizar_trilha_keeps_unchanged_fields() -> None:
    trilha = _make_trilha("Título", 3)
    repo = FakeTrilhaRepo([trilha])
    use_case = UpdateTrack(repo)
    updated = await use_case.execute(trilha.id, None, "Nova desc", None, None)
    assert updated.titulo == "Título"
    assert updated.descricao == "Nova desc"
    assert updated.ordem == 3


# ── DeleteTrack ──────────────────────────────────────────────────────────────

async def test_remover_trilha_removes_it() -> None:
    trilha = _make_trilha()
    repo = FakeTrilhaRepo([trilha])
    use_case = DeleteTrack(repo)
    await use_case.execute(trilha.id)
    assert repo._trilhas == []


async def test_remover_trilha_not_found_raises() -> None:
    repo = FakeTrilhaRepo()
    use_case = DeleteTrack(repo)
    with pytest.raises(TrackNotFound):
        await use_case.execute(uuid4())


# ── ReorderTracks ───────────────────────────────────────────────────────────

async def test_reordenar_calls_repo() -> None:
    repo = FakeTrilhaRepo()
    use_case = ReorderTracks(repo)
    id1, id2 = uuid4(), uuid4()
    await use_case.execute([(id1, 0), (id2, 1)])
    assert repo.reorder_calls == [[(id1, 0), (id2, 1)]]


# ── ListTracksWithProgress ──────────────────────────────────────────────────

async def test_listar_trilhas_progresso_zero_aulas() -> None:
    trilha = _make_trilha()
    trilha_repo = FakeTrilhaRepo([trilha])
    modulo_repo = FakeModuloRepo()
    aula_repo = FakeAulaRepo()
    aluno_repo = FakeAlunoAulaRepo()

    use_case = ListTracksWithProgress(trilha_repo, modulo_repo, aula_repo, aluno_repo)
    result = await use_case.execute(uuid4())

    assert len(result) == 1
    assert result[0].progresso_pct == 0.0
    assert result[0].total_aulas == 0


async def test_listar_trilhas_progresso_partial() -> None:
    trilha = _make_trilha()
    modulo = Module(id=uuid4(), trilha_id=trilha.id, titulo="M1", descricao=None, ordem=0)
    aula1 = Lesson(
        id=uuid4(), modulo_id=modulo.id, titulo="A1", descricao=None,
        drive_file_id="x", duracao_minutos=None, ordem=0, criado_em=datetime.now(tz=UTC)
    )
    aula2 = Lesson(
        id=uuid4(), modulo_id=modulo.id, titulo="A2", descricao=None,
        drive_file_id="y", duracao_minutos=None, ordem=1, criado_em=datetime.now(tz=UTC)
    )

    trilha_repo = FakeTrilhaRepo([trilha])
    modulo_repo = FakeModuloRepo([modulo])
    aula_repo = FakeAulaRepo([aula1, aula2])
    aluno_repo = FakeAlunoAulaRepo({aula1.id})

    use_case = ListTracksWithProgress(trilha_repo, modulo_repo, aula_repo, aluno_repo)
    result = await use_case.execute(uuid4())

    assert result[0].aulas_concluidas == 1
    assert result[0].total_aulas == 2
    assert result[0].progresso_pct == 50.0
