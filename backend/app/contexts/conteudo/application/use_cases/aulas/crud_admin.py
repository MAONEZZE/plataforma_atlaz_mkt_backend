from uuid import UUID, uuid4

from app.contexts.conteudo.domain.entities import Aula
from app.contexts.conteudo.domain.exceptions import AulaNaoEncontrada
from app.contexts.conteudo.domain.repositories import AulaRepository
from app.contexts.conteudo.domain.rules import parse_drive_file_id
from app.shared.utils import now_sp


class CriarAula:
    def __init__(self, repo: AulaRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        modulo_id: UUID,
        titulo: str,
        descricao: str | None,
        drive_url: str,
        duracao_minutos: int | None,
        ordem: int,
    ) -> Aula:
        drive_file_id = parse_drive_file_id(drive_url)
        aula = Aula(
            id=uuid4(),
            modulo_id=modulo_id,
            titulo=titulo,
            descricao=descricao,
            drive_file_id=drive_file_id,
            duracao_minutos=duracao_minutos,
            ordem=ordem,
            criado_em=now_sp(),
        )
        return await self._repo.criar(aula)


class AtualizarAula:
    def __init__(self, repo: AulaRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        aula_id: UUID,
        titulo: str | None,
        descricao: str | None,
        drive_url: str | None,
        duracao_minutos: int | None,
        ordem: int | None,
    ) -> Aula:
        aula = await self._repo.por_id(aula_id)
        if aula is None:
            raise AulaNaoEncontrada(f"Aula {aula_id} não encontrada.")

        drive_file_id = parse_drive_file_id(drive_url) if drive_url else aula.drive_file_id

        updated = Aula(
            id=aula.id,
            modulo_id=aula.modulo_id,
            titulo=titulo if titulo is not None else aula.titulo,
            descricao=descricao if descricao is not None else aula.descricao,
            drive_file_id=drive_file_id,
            duracao_minutos=(
                duracao_minutos if duracao_minutos is not None else aula.duracao_minutos
            ),
            ordem=ordem if ordem is not None else aula.ordem,
            criado_em=aula.criado_em,
        )
        return await self._repo.atualizar(updated)


class RemoverAula:
    def __init__(self, repo: AulaRepository) -> None:
        self._repo = repo

    async def execute(self, aula_id: UUID) -> None:
        aula = await self._repo.por_id(aula_id)
        if aula is None:
            raise AulaNaoEncontrada(f"Aula {aula_id} não encontrada.")
        await self._repo.remover(aula_id)


class ReordenarAulas:
    def __init__(self, repo: AulaRepository) -> None:
        self._repo = repo

    async def execute(self, ordens: list[tuple[UUID, int]]) -> None:
        await self._repo.reordenar(ordens)
