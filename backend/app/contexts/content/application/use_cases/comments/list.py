from uuid import UUID

from app.contexts.conteudo.application.dtos import AutorDTO, ComentarioDTO
from app.contexts.conteudo.domain.repositories import ComentarioRepository
from app.shared.application.dtos import PagedResponse


class ListarComentarios:
    def __init__(self, repo: ComentarioRepository) -> None:
        self._repo = repo

    async def execute(
        self, aula_id: UUID, page: int, page_size: int, current_user_id: UUID
    ) -> PagedResponse[ComentarioDTO]:
        items, total = await self._repo.listar_por_aula(aula_id, page, page_size)
        dtos = [
            ComentarioDTO(
                id=c.id,
                autor=AutorDTO(id=c.usuario_id, nome=c.autor_nome, foto_url=c.autor_foto_url),
                texto=c.texto,
                criado_em=c.criado_em,
                editado_em=c.editado_em,
                apagado_em=c.apagado_em,
                is_proprio=c.usuario_id == current_user_id,
            )
            for c in items
        ]
        return PagedResponse(items=dtos, page=page, page_size=page_size, total=total)
