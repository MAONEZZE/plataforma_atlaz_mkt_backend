from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class TrilhaProgressoDTO:
    id: UUID
    titulo: str
    descricao: str | None
    capa_url: str | None
    total_aulas: int
    aulas_concluidas: int
    progresso_pct: float


@dataclass
class AulaResumoDTO:
    id: UUID
    titulo: str
    duracao_minutos: int | None
    ordem: int
    concluida: bool


@dataclass
class ModuloComAulasDTO:
    id: UUID
    titulo: str
    descricao: str | None
    ordem: int
    aulas: list[AulaResumoDTO]


@dataclass
class TrilhaComModulosDTO:
    id: UUID
    titulo: str
    descricao: str | None
    capa_url: str | None
    progresso_pct: float
    modulos: list[ModuloComAulasDTO]


@dataclass
class TrilhaResumoDTO:
    id: UUID
    titulo: str


@dataclass
class AulaDetalheDTO:
    id: UUID
    modulo_id: UUID
    titulo: str
    descricao: str | None
    drive_file_id: str
    duracao_minutos: int | None
    concluida: bool
    trilha: TrilhaResumoDTO
    proxima_aula: AulaResumoDTO | None


@dataclass
class AutorDTO:
    id: UUID
    nome: str
    foto_url: str | None


@dataclass
class ComentarioDTO:
    id: UUID
    autor: AutorDTO
    texto: str | None
    criado_em: datetime
    editado_em: datetime | None
    apagado_em: datetime | None
    is_proprio: bool
