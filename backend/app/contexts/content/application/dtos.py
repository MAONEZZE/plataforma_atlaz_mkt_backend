from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class TrackProgressDTO:
    id: UUID
    titulo: str
    descricao: str | None
    capa_url: str | None
    total_aulas: int
    aulas_concluidas: int
    progresso_pct: float


@dataclass
class LessonSummaryDTO:
    id: UUID
    titulo: str
    duracao_minutos: int | None
    ordem: int
    concluida: bool


@dataclass
class ModuleWithLessonsDTO:
    id: UUID
    titulo: str
    descricao: str | None
    ordem: int
    aulas: list[LessonSummaryDTO]


@dataclass
class TrackWithModulesDTO:
    id: UUID
    titulo: str
    descricao: str | None
    capa_url: str | None
    progresso_pct: float
    modulos: list[ModuleWithLessonsDTO]


@dataclass
class TrackSummaryDTO:
    id: UUID
    titulo: str


@dataclass
class LessonDetailDTO:
    id: UUID
    modulo_id: UUID
    titulo: str
    descricao: str | None
    drive_file_id: str
    duracao_minutos: int | None
    concluida: bool
    trilha: TrackSummaryDTO
    proxima_aula: LessonSummaryDTO | None


@dataclass
class AutorDTO:
    id: UUID
    nome: str
    foto_url: str | None


@dataclass
class CommentDTO:
    id: UUID
    autor: AutorDTO
    texto: str | None
    criado_em: datetime
    editado_em: datetime | None
    apagado_em: datetime | None
    is_proprio: bool
