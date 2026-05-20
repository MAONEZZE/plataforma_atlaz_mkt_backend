from app.contexts.comunidade.application.dtos import ListarComunidadeResultDTO, MembroComunidadeDTO
from app.contexts.comunidade.domain.repositories import ComunidadeRepository


class ListarComunidade:
    def __init__(self, repo: ComunidadeRepository) -> None:
        self._repo = repo

    async def execute(self, page: int, page_size: int) -> ListarComunidadeResultDTO:
        membros, total = await self._repo.listar_ativos(page=page, page_size=page_size)
        return ListarComunidadeResultDTO(
            items=[
                MembroComunidadeDTO(
                    id=m.id,
                    nome=m.nome,
                    foto_url=m.foto_url,
                    linkedin_url=m.linkedin_url,
                    instagram_username=m.instagram_username,
                )
                for m in membros
            ],
            page=page,
            page_size=page_size,
            total=total,
        )
