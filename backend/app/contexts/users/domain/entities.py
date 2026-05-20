from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class User:
    id: UUID
    nome: str
    email: str
    telefone: str | None
    linkedin_url: str | None
    instagram_username: str | None
    descricao: str | None
    foto_url: str | None
    role: str
    inativo: bool
    criado_em: datetime
    atualizado_em: datetime
