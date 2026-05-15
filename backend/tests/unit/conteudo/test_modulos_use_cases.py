from uuid import UUID, uuid4

import pytest

from app.contexts.conteudo.application.use_cases.modulos.crud_admin import (
    AtualizarModulo,
    CriarModulo,
    RemoverModulo,
    ReordenarModulos,
)
from app.contexts.conteudo.domain.entities import Modulo
from app.contexts.conteudo.domain.exceptions import ModuloNaoEncontrado


class FakeModuloRepo:
    def __init__(self, modulos: list[Modulo] | None = None) -> None:
        self._modulos: list[Modulo] = modulos or []
        self.reorder_calls: list[list[tuple[UUID, int]]] = []

    async def por_id(self, modulo_id: UUID) -> Modulo | None:
        return next((m for m in self._modulos if m.id == modulo_id), None)

    async def criar(self, modulo: Modulo) -> Modulo:
        self._modulos.append(modulo)
        return modulo

    async def atualizar(self, modulo: Modulo) -> Modulo:
        self._modulos = [modulo if m.id == modulo.id else m for m in self._modulos]
        return modulo

    async def remover(self, modulo_id: UUID) -> None:
        self._modulos = [m for m in self._modulos if m.id != modulo_id]

    async def reordenar(self, ordens: list[tuple[UUID, int]]) -> None:
        self.reorder_calls.append(ordens)


def _make_modulo(titulo: str = "Módulo", ordem: int = 0) -> Modulo:
    return Modulo(id=uuid4(), trilha_id=uuid4(), titulo=titulo, descricao=None, ordem=ordem)


async def test_criar_modulo_ok() -> None:
    repo = FakeModuloRepo()
    use_case = CriarModulo(repo)
    trilha_id = uuid4()
    modulo = await use_case.execute(trilha_id, "Intro", None, 0)
    assert modulo.titulo == "Intro"
    assert modulo.trilha_id == trilha_id


async def test_atualizar_modulo_not_found_raises() -> None:
    use_case = AtualizarModulo(FakeModuloRepo())
    with pytest.raises(ModuloNaoEncontrado):
        await use_case.execute(uuid4(), "X", None, None)


async def test_atualizar_modulo_keeps_unchanged_fields() -> None:
    modulo = _make_modulo("Original", 2)
    repo = FakeModuloRepo([modulo])
    use_case = AtualizarModulo(repo)
    updated = await use_case.execute(modulo.id, None, "Nova desc", None)
    assert updated.titulo == "Original"
    assert updated.descricao == "Nova desc"
    assert updated.ordem == 2


async def test_remover_modulo_not_found_raises() -> None:
    use_case = RemoverModulo(FakeModuloRepo())
    with pytest.raises(ModuloNaoEncontrado):
        await use_case.execute(uuid4())


async def test_remover_modulo_ok() -> None:
    modulo = _make_modulo()
    repo = FakeModuloRepo([modulo])
    use_case = RemoverModulo(repo)
    await use_case.execute(modulo.id)
    assert repo._modulos == []


async def test_reordenar_modulos_calls_repo() -> None:
    repo = FakeModuloRepo()
    use_case = ReordenarModulos(repo)
    ids = [(uuid4(), i) for i in range(3)]
    await use_case.execute(ids)
    assert repo.reorder_calls == [ids]
