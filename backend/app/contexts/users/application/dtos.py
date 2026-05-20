from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class UserDTO:
    id: UUID
    nome: str
    email: str
    telefone: str | None
    linkedin_url: str | None
    instagram_username: str | None
    descricao: str | None
    foto_url: str | None
    role: str
    criado_em: datetime


@dataclass(frozen=True)
class UpdateMeInput:
    nome: str | None
    telefone: str | None
    linkedin_url: str | None
    instagram_username: str | None
    descricao: str | None = None


@dataclass(frozen=True)
class UploadPhotoInput:
    usuario_id: UUID
    content_type: str
    data: bytes


@dataclass(frozen=True)
class PhotoUrlDTO:
    foto_url: str
