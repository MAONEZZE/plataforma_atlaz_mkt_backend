from uuid import UUID

from app.contexts.conteudo.application.dtos import TrilhaProgressoDTO
from app.contexts.conteudo.domain.repositories import (
    AlunoAulaRepository,
    AulaRepository,
    ModuloRepository,
    TrilhaRepository,
)


class ListarTrilhasComProgresso:
    def __init__(
        self,
        trilha_repo: TrilhaRepository,
        modulo_repo: ModuloRepository,
        aula_repo: AulaRepository,
        aluno_aula_repo: AlunoAulaRepository,
    ) -> None:
        self._trilha_repo = trilha_repo
        self._modulo_repo = modulo_repo
        self._aula_repo = aula_repo
        self._aluno_aula_repo = aluno_aula_repo

    async def execute(self, usuario_id: UUID) -> list[TrilhaProgressoDTO]:
        trilhas = await self._trilha_repo.listar()
        concluidas = await self._aluno_aula_repo.concluidas_ids(usuario_id)

        result = []
        for trilha in trilhas:
            modulos = await self._modulo_repo.listar_por_trilha(trilha.id)
            all_aulas = []
            for modulo in modulos:
                aulas = await self._aula_repo.listar_por_modulo(modulo.id)
                all_aulas.extend(aulas)

            total = len(all_aulas)
            concluidas_count = sum(1 for a in all_aulas if a.id in concluidas)
            pct = round(concluidas_count / total * 100, 2) if total > 0 else 0.0

            result.append(
                TrilhaProgressoDTO(
                    id=trilha.id,
                    titulo=trilha.titulo,
                    descricao=trilha.descricao,
                    capa_url=trilha.capa_url,
                    total_aulas=total,
                    aulas_concluidas=concluidas_count,
                    progresso_pct=pct,
                )
            )
        return result
