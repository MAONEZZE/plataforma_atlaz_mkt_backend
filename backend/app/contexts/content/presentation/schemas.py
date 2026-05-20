from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ── Trilha schemas ─────────────────────────────────────────────────────────────


class TrackProgressOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    titulo: str
    descricao: str | None
    capa_url: str | None
    total_aulas: int
    aulas_concluidas: int
    progresso_pct: float


class LessonSummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    titulo: str
    duracao_minutos: int | None
    ordem: int
    concluida: bool


class ModuleWithLessonsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    titulo: str
    descricao: str | None
    ordem: int
    aulas: list[LessonSummaryOut]


class TrackResumoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    titulo: str


class TrackWithModulesOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    titulo: str
    descricao: str | None
    capa_url: str | None
    progresso_pct: float
    modulos: list[ModuloComAulasOut]


# ── Aula schemas ───────────────────────────────────────────────────────────────


class LessonDetailOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    modulo_id: UUID
    titulo: str
    descricao: str | None
    drive_file_id: str
    duracao_minutos: int | None
    concluida: bool
    trilha: TrackResumoOut
    proxima_aula: LessonResumoOut | None


# ── Admin input schemas ────────────────────────────────────────────────────────


class CreateTrackIn(BaseModel):
    titulo: str
    descricao: str | None = None
    capa_url: str | None = None
    ordem: int = 0


class UpdateTrackIn(BaseModel):
    titulo: str | None = None
    descricao: str | None = None
    capa_url: str | None = None
    ordem: int | None = None


class OrdemItem(BaseModel):
    id: UUID
    ordem: int


class ReordenarIn(BaseModel):
    ordem: list[OrdemItem]


class CreateModuleIn(BaseModel):
    trilha_id: UUID
    titulo: str
    descricao: str | None = None
    ordem: int = 0


class UpdateModuleIn(BaseModel):
    titulo: str | None = None
    descricao: str | None = None
    ordem: int | None = None


class CreateLessonIn(BaseModel):
    modulo_id: UUID
    titulo: str
    descricao: str | None = None
    drive_url: str
    duracao_minutos: int | None = None
    ordem: int = 0


class UpdateLessonIn(BaseModel):
    titulo: str | None = None
    descricao: str | None = None
    drive_url: str | None = None
    duracao_minutos: int | None = None
    ordem: int | None = None


# ── Admin output schemas ───────────────────────────────────────────────────────


class TrackAdminOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    titulo: str
    descricao: str | None
    capa_url: str | None
    ordem: int
    criado_em: datetime


class ModuleAdminOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    trilha_id: UUID
    titulo: str
    descricao: str | None
    ordem: int


class LessonAdminOut(BaseModel):
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


class CommentOut(BaseModel):
    id: UUID
    autor: AutorOut
    texto: str | None
    criado_em: datetime
    editado_em: datetime | None
    apagado_em: datetime | None
    is_proprio: bool


class CreateCommentIn(BaseModel):
    texto: str = Field(..., min_length=1, max_length=2000)


class EditCommentIn(BaseModel):
    texto: str = Field(..., min_length=1, max_length=2000)
