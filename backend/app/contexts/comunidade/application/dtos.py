from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class MembroComunidadeDTO:
    id: UUID
    nome: str
    foto_url: str | None
    linkedin_url: str | None
    instagram_username: str | None


@dataclass(frozen=True)
class ListarComunidadeResultDTO:
    items: list[MembroComunidadeDTO]
    page: int
    page_size: int
    total: int
