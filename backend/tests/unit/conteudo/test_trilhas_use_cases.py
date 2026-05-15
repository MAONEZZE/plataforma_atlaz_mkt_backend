from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from app.contexts.conteudo.application.use_cases.trilhas.crud_admin import (
    AtualizarTrilha,
    CriarTrilha,
    RemoverTrilha,
    ReordenarTrilhas,
)
from app.contexts.conteudo.application.use_cases.trilhas.listar_com_progresso import (
    ListarTrilhasComProgresso,
)
from app.contexts.conteudo.domain.entities import Aula, Modulo, Trilha
from app.contexts.conteudo.domain.exceptions import TrilhaNaoEncontrada


# ── Fake repos ─────────────────────────────────────────────────────────────────

class FakeTrilhaRepo:
    def __init__(self, trilhas: list[Trilha] | None = None) -> None:
        self._trilhas: list[Trilha] = trilhas or []
        self.reorder_calls: list[list[tuple[UUID, int]]] = []

    async def listar(self) -> list[Trilha]:
        return list(self._trilhas)

    async def por_id(self, trilha_id: UUID) -> Trilha | None:
        return next((t for t in self._trilhas if t.id == trilha_id), None)

    async def criar(self, trilha: Trilha) -> Trilha:
        self._trilhas.append(trilha)
        return trilha

    async def atualizar(self, trilha: Trilha) -> Trilha:
        self._trilhas = [trilha if t.id == trilha.id else t for t in self._trilhas]
        return trilha

    async def remover(self, trilha_id: UUID) -> None:
        self._trilhas = [t for t in self._trilhas if t.id != trilha_id]

    async def reordenar(self, ordens: list[tuple[UUID, int]]) -> None:
        self.reorder_calls.append(ordens)

    async def contar_aulas(self, trilha_id: UUID) -> int:
        return 0


class FakeModuloRepo:
    def __init__(self, modulos: list[Modulo] | None = None) -> None:
        self._modulos = modulos or []

    async def listar_por_trilha(self, trilha_id: UUID) -> list[Modulo]:
        return [m for m in self._modulos if m.trilha_id == trilha_id]


class FakeAulaRepo:
    def __init__(self, aulas: list[Aula] | None = None) -> None:
        self._aulas = aulas or []

    async def listar_por_modulo(self, modulo_id: UUID) -> list[Aula]:
        return [a for a in self._aulas if a.modulo_id == modulo_id]


class FakeAlunoAulaRepo:
    def __init__(self, concluidas: set[UUID] | None = None) -> None:
        self._concluidas: set[UUID] = concluidas or set()

    async def concluidas_ids(self, usuario_id: UUID) -> set[UUID]:
        return self._concluidas


# ── CriarTrilha ────────────────────────────────────────────────────────────────

async def test_criar_trilha_returns_trilha() -> None:
    repo = FakeTrilhaRepo()
    use_case = CriarTrilha(repo)
    trilha = await use_case.execute("Prospecção", "desc", None, 0)
    assert trilha.titulo == "Prospecção"
    assert trilha.ordem == 0
    assert len(repo._trilhas) == 1


async def test_criar_trilha_generates_uuid() -> None:
    repo = FakeTrilhaRepo()
    use_case = CriarTrilha(repo)
    t1 = await use_case.execute("T1", None, None, 0)
    t2 = await use_case.execute("T2", None, None, 0)
    assert t1.id != t2.id


# ── AtualizarTrilha ────────────────────────────────────────────────────────────

def _make_trilha(titulo: str = "Trilha", ordem: int = 0) -> Trilha:
    return Trilha(
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
    use_case = AtualizarTrilha(repo)
    updated = await use_case.execute(trilha.id, "Nova", None, None, None)
    assert updated.titulo == "Nova"


async def test_atualizar_trilha_not_found_raises() -> None:
    repo = FakeTrilhaRepo()
    use_case = AtualizarTrilha(repo)
    with pytest.raises(TrilhaNaoEncontrada):
        await use_case.execute(uuid4(), "X", None, None, None)


async def test_atualizar_trilha_keeps_unchanged_fields() -> None:
    trilha = _make_trilha("Título", 3)
    repo = FakeTrilhaRepo([trilha])
    use_case = AtualizarTrilha(repo)
    updated = await use_case.execute(trilha.id, None, "Nova desc", None, None)
    assert updated.titulo == "Título"
    assert updated.descricao == "Nova desc"
    assert updated.ordem == 3


# ── RemoverTrilha ──────────────────────────────────────────────────────────────

async def test_remover_trilha_removes_it() -> None:
    trilha = _make_trilha()
    repo = FakeTrilhaRepo([trilha])
    use_case = RemoverTrilha(repo)
    await use_case.execute(trilha.id)
    assert repo._trilhas == []


async def test_remover_trilha_not_found_raises() -> None:
    repo = FakeTrilhaRepo()
    use_case = RemoverTrilha(repo)
    with pytest.raises(TrilhaNaoEncontrada):
        await use_case.execute(uuid4())


# ── ReordenarTrilhas ───────────────────────────────────────────────────────────

async def test_reordenar_calls_repo() -> None:
    repo = FakeTrilhaRepo()
    use_case = ReordenarTrilhas(repo)
    id1, id2 = uuid4(), uuid4()
    await use_case.execute([(id1, 0), (id2, 1)])
    assert repo.reorder_calls == [[(id1, 0), (id2, 1)]]


# ── ListarTrilhasComProgresso ──────────────────────────────────────────────────

async def test_listar_trilhas_progresso_zero_aulas() -> None:
    trilha = _make_trilha()
    trilha_repo = FakeTrilhaRepo([trilha])
    modulo_repo = FakeModuloRepo()
    aula_repo = FakeAulaRepo()
    aluno_repo = FakeAlunoAulaRepo()

    use_case = ListarTrilhasComProgresso(trilha_repo, modulo_repo, aula_repo, aluno_repo)
    result = await use_case.execute(uuid4())

    assert len(result) == 1
    assert result[0].progresso_pct == 0.0
    assert result[0].total_aulas == 0


async def test_listar_trilhas_progresso_partial() -> None:
    trilha = _make_trilha()
    modulo = Modulo(id=uuid4(), trilha_id=trilha.id, titulo="M1", descricao=None, ordem=0)
    aula1 = Aula(
        id=uuid4(), modulo_id=modulo.id, titulo="A1", descricao=None,
        drive_file_id="x", duracao_minutos=None, ordem=0, criado_em=datetime.now(tz=UTC)
    )
    aula2 = Aula(
        id=uuid4(), modulo_id=modulo.id, titulo="A2", descricao=None,
        drive_file_id="y", duracao_minutos=None, ordem=1, criado_em=datetime.now(tz=UTC)
    )

    trilha_repo = FakeTrilhaRepo([trilha])
    modulo_repo = FakeModuloRepo([modulo])
    aula_repo = FakeAulaRepo([aula1, aula2])
    aluno_repo = FakeAlunoAulaRepo({aula1.id})

    use_case = ListarTrilhasComProgresso(trilha_repo, modulo_repo, aula_repo, aluno_repo)
    result = await use_case.execute(uuid4())

    assert result[0].aulas_concluidas == 1
    assert result[0].total_aulas == 2
    assert result[0].progresso_pct == 50.0
