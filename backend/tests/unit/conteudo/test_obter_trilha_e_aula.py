from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from app.contexts.conteudo.application.use_cases.aulas.obter import ObterAula
from app.contexts.conteudo.application.use_cases.trilhas.obter_com_modulos import (
    ObterTrilhaComModulos,
)
from app.contexts.conteudo.domain.entities import Aula, Modulo, Trilha
from app.contexts.conteudo.domain.exceptions import AulaNaoEncontrada, TrilhaNaoEncontrada


# ── Fake repos ─────────────────────────────────────────────────────────────────

class FakeTrilhaRepo:
    def __init__(self, trilhas: list[Trilha] | None = None) -> None:
        self._trilhas = trilhas or []

    async def listar(self) -> list[Trilha]:
        return list(self._trilhas)

    async def por_id(self, trilha_id: UUID) -> Trilha | None:
        return next((t for t in self._trilhas if t.id == trilha_id), None)


class FakeModuloRepo:
    def __init__(self, modulos: list[Modulo] | None = None) -> None:
        self._modulos = modulos or []

    async def listar_por_trilha(self, trilha_id: UUID) -> list[Modulo]:
        return [m for m in self._modulos if m.trilha_id == trilha_id]

    async def por_id(self, modulo_id: UUID) -> Modulo | None:
        return next((m for m in self._modulos if m.id == modulo_id), None)


class FakeAulaRepo:
    def __init__(self, aulas: list[Aula] | None = None) -> None:
        self._aulas = aulas or []

    async def por_id(self, aula_id: UUID) -> Aula | None:
        return next((a for a in self._aulas if a.id == aula_id), None)

    async def listar_por_modulo(self, modulo_id: UUID) -> list[Aula]:
        return [a for a in self._aulas if a.modulo_id == modulo_id]

    async def proxima(self, aula: Aula) -> Aula | None:
        same_modulo = sorted(
            [a for a in self._aulas if a.modulo_id == aula.modulo_id and a.ordem > aula.ordem],
            key=lambda a: a.ordem,
        )
        return same_modulo[0] if same_modulo else None


class FakeAlunoAulaRepo:
    def __init__(self, concluidas: set[UUID] | None = None) -> None:
        self._concluidas: set[UUID] = concluidas or set()

    async def concluidas_ids(self, usuario_id: UUID) -> set[UUID]:
        return self._concluidas


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_trilha() -> Trilha:
    return Trilha(
        id=uuid4(), titulo="T", descricao=None, capa_url=None,
        ordem=0, criado_em=datetime.now(tz=UTC)
    )


def _make_modulo(trilha_id: UUID, ordem: int = 0) -> Modulo:
    return Modulo(id=uuid4(), trilha_id=trilha_id, titulo="M", descricao=None, ordem=ordem)


def _make_aula(modulo_id: UUID, ordem: int = 0) -> Aula:
    return Aula(
        id=uuid4(), modulo_id=modulo_id, titulo="A", descricao=None,
        drive_file_id="x", duracao_minutos=None, ordem=ordem, criado_em=datetime.now(tz=UTC)
    )


# ── ObterTrilhaComModulos ──────────────────────────────────────────────────────

async def test_obter_trilha_not_found_raises() -> None:
    use_case = ObterTrilhaComModulos(
        FakeTrilhaRepo(), FakeModuloRepo(), FakeAulaRepo(), FakeAlunoAulaRepo()
    )
    with pytest.raises(TrilhaNaoEncontrada):
        await use_case.execute(uuid4(), uuid4())


async def test_obter_trilha_com_modulos_estrutura() -> None:
    trilha = _make_trilha()
    modulo = _make_modulo(trilha.id)
    aula = _make_aula(modulo.id)

    use_case = ObterTrilhaComModulos(
        FakeTrilhaRepo([trilha]),
        FakeModuloRepo([modulo]),
        FakeAulaRepo([aula]),
        FakeAlunoAulaRepo({aula.id}),
    )
    dto = await use_case.execute(trilha.id, uuid4())

    assert dto.id == trilha.id
    assert len(dto.modulos) == 1
    assert len(dto.modulos[0].aulas) == 1
    assert dto.modulos[0].aulas[0].concluida is True
    assert dto.progresso_pct == 100.0


async def test_obter_trilha_progresso_zero() -> None:
    trilha = _make_trilha()
    modulo = _make_modulo(trilha.id)
    aula = _make_aula(modulo.id)

    use_case = ObterTrilhaComModulos(
        FakeTrilhaRepo([trilha]),
        FakeModuloRepo([modulo]),
        FakeAulaRepo([aula]),
        FakeAlunoAulaRepo(),
    )
    dto = await use_case.execute(trilha.id, uuid4())
    assert dto.progresso_pct == 0.0
    assert dto.modulos[0].aulas[0].concluida is False


# ── ObterAula ──────────────────────────────────────────────────────────────────

async def test_obter_aula_not_found_raises() -> None:
    use_case = ObterAula(FakeAulaRepo(), FakeModuloRepo(), FakeTrilhaRepo(), FakeAlunoAulaRepo())
    with pytest.raises(AulaNaoEncontrada):
        await use_case.execute(uuid4(), uuid4())


async def test_obter_aula_com_proxima() -> None:
    trilha = _make_trilha()
    modulo = _make_modulo(trilha.id)
    aula1 = _make_aula(modulo.id, ordem=0)
    aula2 = _make_aula(modulo.id, ordem=1)

    use_case = ObterAula(
        FakeAulaRepo([aula1, aula2]),
        FakeModuloRepo([modulo]),
        FakeTrilhaRepo([trilha]),
        FakeAlunoAulaRepo(),
    )
    dto = await use_case.execute(aula1.id, uuid4())
    assert dto.proxima_aula is not None
    assert dto.proxima_aula.id == aula2.id


async def test_obter_aula_ultima_proxima_none() -> None:
    trilha = _make_trilha()
    modulo = _make_modulo(trilha.id)
    aula = _make_aula(modulo.id)

    use_case = ObterAula(
        FakeAulaRepo([aula]),
        FakeModuloRepo([modulo]),
        FakeTrilhaRepo([trilha]),
        FakeAlunoAulaRepo(),
    )
    dto = await use_case.execute(aula.id, uuid4())
    assert dto.proxima_aula is None


async def test_obter_aula_concluida_flag() -> None:
    trilha = _make_trilha()
    modulo = _make_modulo(trilha.id)
    aula = _make_aula(modulo.id)

    use_case = ObterAula(
        FakeAulaRepo([aula]),
        FakeModuloRepo([modulo]),
        FakeTrilhaRepo([trilha]),
        FakeAlunoAulaRepo({aula.id}),
    )
    dto = await use_case.execute(aula.id, uuid4())
    assert dto.concluida is True
    assert dto.trilha.id == trilha.id
