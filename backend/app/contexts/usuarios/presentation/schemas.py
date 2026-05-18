from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PatchMeBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nome: str | None = None
    telefone: str | None = None
    linkedin_url: str | None = None
    instagram_username: str | None = None
    descricao: str | None = None


class UsuarioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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


class FotoUrlResponse(BaseModel):
    foto_url: str
