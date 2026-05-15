from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class UsuarioDTO:
    id: UUID
    nome: str
    email: str
    telefone: str | None
    linkedin_url: str | None
    instagram_username: str | None
    foto_url: str | None
    role: str
    criado_em: datetime


@dataclass(frozen=True)
class AtualizarMeInput:
    nome: str | None
    telefone: str | None
    linkedin_url: str | None
    instagram_username: str | None


@dataclass(frozen=True)
class UploadFotoInput:
    usuario_id: UUID
    content_type: str
    data: bytes


@dataclass(frozen=True)
class FotoUrlDTO:
    foto_url: str
