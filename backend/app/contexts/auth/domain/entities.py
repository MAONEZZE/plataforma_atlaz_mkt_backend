from dataclasses import dataclass
from uuid import UUID


@dataclass
class Usuario:
    id: UUID
    email: str
    role: str
    inativo: bool
