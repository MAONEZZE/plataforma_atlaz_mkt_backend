from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ── Trilha schemas ─────────────────────────────────────────────────────────────


class TrilhaProgressoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    titulo: str
    descricao: str | None
    capa_url: str | None
    total_aulas: int
    aulas_concluidas: int
    progresso_pct: float


class AulaResumoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    titulo: str
    duracao_minutos: int | None
    ordem: int
    concluida: bool


class ModuloComAulasOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    titulo: str
    descricao: str | None
    ordem: int
    aulas: list[AulaResumoOut]


class TrilhaResumoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    titulo: str


class TrilhaComModulosOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    titulo: str
    descricao: str | None
    capa_url: str | None
    progresso_pct: float
    modulos: list[ModuloComAulasOut]


# ── Aula schemas ───────────────────────────────────────────────────────────────


class AulaDetalheOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    modulo_id: UUID
    titulo: str
    descricao: str | None
    drive_file_id: str
    duracao_minutos: int | None
    concluida: bool
    trilha: TrilhaResumoOut
    proxima_aula: AulaResumoOut | None


# ── Admin input schemas ────────────────────────────────────────────────────────


class CriarTrilhaIn(BaseModel):
    titulo: str
    descricao: str | None = None
    capa_url: str | None = None
    ordem: int = 0


class AtualizarTrilhaIn(BaseModel):
    titulo: str | None = None
    descricao: str | None = None
    capa_url: str | None = None
    ordem: int | None = None


class OrdemItem(BaseModel):
    id: UUID
    ordem: int


class ReordenarIn(BaseModel):
    ordem: list[OrdemItem]


class CriarModuloIn(BaseModel):
    trilha_id: UUID
    titulo: str
    descricao: str | None = None
    ordem: int = 0


class AtualizarModuloIn(BaseModel):
    titulo: str | None = None
    descricao: str | None = None
    ordem: int | None = None


class CriarAulaIn(BaseModel):
    modulo_id: UUID
    titulo: str
    descricao: str | None = None
    drive_url: str
    duracao_minutos: int | None = None
    ordem: int = 0


class AtualizarAulaIn(BaseModel):
    titulo: str | None = None
    descricao: str | None = None
    drive_url: str | None = None
    duracao_minutos: int | None = None
    ordem: int | None = None


# ── Admin output schemas ───────────────────────────────────────────────────────


class TrilhaAdminOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    titulo: str
    descricao: str | None
    capa_url: str | None
    ordem: int
    criado_em: datetime


class ModuloAdminOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    trilha_id: UUID
    titulo: str
    descricao: str | None
    ordem: int


class AulaAdminOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    modulo_id: UUID
    titulo: str
    descricao: str | None
    drive_file_id: str
    duracao_minutos: int | None
    ordem: int
    criado_em: datetime


# ── Comentario schemas ─────────────────────────────────────────────────────────


class AutorOut(BaseModel):
    id: UUID
    nome: str
    foto_url: str | None


class ComentarioOut(BaseModel):
    id: UUID
    autor: AutorOut
    texto: str | None
    criado_em: datetime
    editado_em: datetime | None
    apagado_em: datetime | None
    is_proprio: bool


class CriarComentarioIn(BaseModel):
    texto: str = Field(..., min_length=1, max_length=2000)


class EditarComentarioIn(BaseModel):
    texto: str = Field(..., min_length=1, max_length=2000)
