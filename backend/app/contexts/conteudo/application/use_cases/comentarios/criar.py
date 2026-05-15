from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.contexts.conteudo.domain.entities import Comentario
from app.contexts.conteudo.domain.exceptions import AulaNaoEncontrada
from app.contexts.conteudo.domain.repositories import AulaRepository, ComentarioRepository


class CriarComentario:
    def __init__(self, aula_repo: AulaRepository, comentario_repo: ComentarioRepository) -> None:
        self._aula_repo = aula_repo
        self._comentario_repo = comentario_repo

    async def execute(self, aula_id: UUID, usuario_id: UUID, texto: str) -> Comentario:
        aula = await self._aula_repo.por_id(aula_id)
        if aula is None:
            raise AulaNaoEncontrada(f"Aula {aula_id} não encontrada.")

        comentario = Comentario(
            id=uuid4(),
            aula_id=aula_id,
            usuario_id=usuario_id,
            texto=texto,
            criado_em=datetime.now(tz=UTC),
            editado_em=None,
            apagado_em=None,
        )
        return await self._comentario_repo.criar(comentario)
