from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class Track:
    id: UUID
    titulo: str
    descricao: str | None
    capa_url: str | None
    ordem: int
    criado_em: datetime


@dataclass
class Module:
    id: UUID
    trilha_id: UUID
    titulo: str
    descricao: str | None
    ordem: int


@dataclass
class Lesson:
    id: UUID
    modulo_id: UUID
    titulo: str
    descricao: str | None
    drive_file_id: str
    duracao_minutos: int | None
    ordem: int
    criado_em: datetime


@dataclass
class StudentLesson:
    usuario_id: UUID
    aula_id: UUID
    concluida_em: datetime


@dataclass
class Comment:
    id: UUID
    aula_id: UUID
    usuario_id: UUID
    texto: str
    criado_em: datetime
    editado_em: datetime | None
    apagado_em: datetime | None


@dataclass
class CommentRead:
    """Comentario com dados denormalizados do autor para listagem."""

    id: UUID
    aula_id: UUID
    usuario_id: UUID
    texto: str | None
    criado_em: datetime
    editado_em: datetime | None
    apagado_em: datetime | None
    autor_nome: str
    autor_foto_url: str | None
