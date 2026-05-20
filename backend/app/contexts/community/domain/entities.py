from dataclasses import dataclass
from uuid import UUID


@dataclass
class MembroComunidade:
    id: UUID
    nome: str
    foto_url: str | None
    linkedin_url: str | None
    instagram_username: str | None
