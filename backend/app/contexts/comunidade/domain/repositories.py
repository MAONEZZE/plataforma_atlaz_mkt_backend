from typing import Protocol

from app.contexts.comunidade.domain.entities import MembroComunidade


class ComunidadeRepository(Protocol):
    async def listar_ativos(
        self, page: int, page_size: int
    ) -> tuple[list[MembroComunidade], int]: ...
