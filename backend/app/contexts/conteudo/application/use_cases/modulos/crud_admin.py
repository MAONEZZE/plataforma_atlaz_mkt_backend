from uuid import UUID, uuid4

from app.contexts.conteudo.domain.entities import Modulo
from app.contexts.conteudo.domain.exceptions import ModuloNaoEncontrado
from app.contexts.conteudo.domain.repositories import ModuloRepository


class CriarModulo:
    def __init__(self, repo: ModuloRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        trilha_id: UUID,
        titulo: str,
        descricao: str | None,
        ordem: int,
    ) -> Modulo:
        modulo = Modulo(
            id=uuid4(),
            trilha_id=trilha_id,
            titulo=titulo,
            descricao=descricao,
            ordem=ordem,
        )
        return await self._repo.criar(modulo)


class AtualizarModulo:
    def __init__(self, repo: ModuloRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        modulo_id: UUID,
        titulo: str | None,
        descricao: str | None,
        ordem: int | None,
    ) -> Modulo:
        modulo = await self._repo.por_id(modulo_id)
        if modulo is None:
            raise ModuloNaoEncontrado(f"Módulo {modulo_id} não encontrado.")
        updated = Modulo(
            id=modulo.id,
            trilha_id=modulo.trilha_id,
            titulo=titulo if titulo is not None else modulo.titulo,
            descricao=descricao if descricao is not None else modulo.descricao,
            ordem=ordem if ordem is not None else modulo.ordem,
        )
        return await self._repo.atualizar(updated)


class RemoverModulo:
    def __init__(self, repo: ModuloRepository) -> None:
        self._repo = repo

    async def execute(self, modulo_id: UUID) -> None:
        modulo = await self._repo.por_id(modulo_id)
        if modulo is None:
            raise ModuloNaoEncontrado(f"Módulo {modulo_id} não encontrado.")
        await self._repo.remover(modulo_id)


class ReordenarModulos:
    def __init__(self, repo: ModuloRepository) -> None:
        self._repo = repo

    async def execute(self, ordens: list[tuple[UUID, int]]) -> None:
        await self._repo.reordenar(ordens)
