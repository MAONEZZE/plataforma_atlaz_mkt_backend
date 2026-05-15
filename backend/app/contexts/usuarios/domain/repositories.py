from typing import Protocol
from uuid import UUID

from app.contexts.usuarios.domain.entities import Usuario


class UsuarioRepository(Protocol):
    async def por_id(self, user_id: UUID) -> Usuario | None: ...
    async def atualizar(self, usuario: Usuario) -> Usuario: ...
