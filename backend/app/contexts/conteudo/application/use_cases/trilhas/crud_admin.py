from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.contexts.conteudo.domain.entities import Trilha
from app.contexts.conteudo.domain.exceptions import TrilhaNaoEncontrada
from app.contexts.conteudo.domain.repositories import TrilhaRepository


class CriarTrilha:
    def __init__(self, repo: TrilhaRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        titulo: str,
        descricao: str | None,
        capa_url: str | None,
        ordem: int,
    ) -> Trilha:
        trilha = Trilha(
            id=uuid4(),
            titulo=titulo,
            descricao=descricao,
            capa_url=capa_url,
            ordem=ordem,
            criado_em=datetime.now(tz=UTC),
        )
        return await self._repo.criar(trilha)


class AtualizarTrilha:
    def __init__(self, repo: TrilhaRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        trilha_id: UUID,
        titulo: str | None,
        descricao: str | None,
        capa_url: str | None,
        ordem: int | None,
    ) -> Trilha:
        trilha = await self._repo.por_id(trilha_id)
        if trilha is None:
            raise TrilhaNaoEncontrada(f"Trilha {trilha_id} não encontrada.")
        updated = Trilha(
            id=trilha.id,
            titulo=titulo if titulo is not None else trilha.titulo,
            descricao=descricao if descricao is not None else trilha.descricao,
            capa_url=capa_url if capa_url is not None else trilha.capa_url,
            ordem=ordem if ordem is not None else trilha.ordem,
            criado_em=trilha.criado_em,
        )
        return await self._repo.atualizar(updated)


class RemoverTrilha:
    def __init__(self, repo: TrilhaRepository) -> None:
        self._repo = repo

    async def execute(self, trilha_id: UUID) -> None:
        trilha = await self._repo.por_id(trilha_id)
        if trilha is None:
            raise TrilhaNaoEncontrada(f"Trilha {trilha_id} não encontrada.")
        await self._repo.remover(trilha_id)


class ReordenarTrilhas:
    def __init__(self, repo: TrilhaRepository) -> None:
        self._repo = repo

    async def execute(self, ordens: list[tuple[UUID, int]]) -> None:
        await self._repo.reordenar(ordens)
