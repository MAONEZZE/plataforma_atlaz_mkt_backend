from uuid import UUID

from fastapi import APIRouter, Depends
from starlette import status

from app.contexts.auth.domain.entities import Usuario
from app.contexts.conteudo.application.use_cases.aulas.desmarcar import DesmarcarConcluida
from app.contexts.conteudo.application.use_cases.aulas.marcar_concluida import MarcarConcluida
from app.contexts.conteudo.application.use_cases.aulas.obter import ObterAula
from app.contexts.conteudo.application.use_cases.trilhas.listar_com_progresso import (
    ListarTrilhasComProgresso,
)
from app.contexts.conteudo.application.use_cases.trilhas.obter_com_modulos import (
    ObterTrilhaComModulos,
)
from app.contexts.conteudo.domain.exceptions import (
    AulaNaoEncontrada,
    ModuloNaoEncontrado,
    TrilhaNaoEncontrada,
)
from app.contexts.conteudo.presentation.deps import (
    get_desmarcar_concluida,
    get_listar_trilhas,
    get_marcar_concluida,
    get_obter_aula,
    get_obter_trilha,
)
from app.contexts.conteudo.presentation.schemas import (
    AulaDetalheOut,
    AulaResumoOut,
    ModuloComAulasOut,
    TrilhaComModulosOut,
    TrilhaProgressoOut,
    TrilhaResumoOut,
)
from app.core.deps import get_current_user
from app.core.exceptions import AppException

router = APIRouter(tags=["conteudo"])


@router.get("/trilhas", response_model=list[TrilhaProgressoOut])
async def listar_trilhas(
    user: Usuario = Depends(get_current_user),
    use_case: ListarTrilhasComProgresso = Depends(get_listar_trilhas),
) -> list[TrilhaProgressoOut]:
    dtos = await use_case.execute(user.id)
    return [
        TrilhaProgressoOut(
            id=d.id,
            titulo=d.titulo,
            descricao=d.descricao,
            capa_url=d.capa_url,
            total_aulas=d.total_aulas,
            aulas_concluidas=d.aulas_concluidas,
            progresso_pct=d.progresso_pct,
        )
        for d in dtos
    ]


@router.get("/trilhas/{trilha_id}", response_model=TrilhaComModulosOut)
async def obter_trilha(
    trilha_id: UUID,
    user: Usuario = Depends(get_current_user),
    use_case: ObterTrilhaComModulos = Depends(get_obter_trilha),
) -> TrilhaComModulosOut:
    try:
        dto = await use_case.execute(trilha_id, user.id)
    except TrilhaNaoEncontrada as exc:
        raise AppException("TRILHA_NOT_FOUND", str(exc), 404) from exc
    return TrilhaComModulosOut(
        id=dto.id,
        titulo=dto.titulo,
        descricao=dto.descricao,
        capa_url=dto.capa_url,
        progresso_pct=dto.progresso_pct,
        modulos=[
            ModuloComAulasOut(
                id=m.id,
                titulo=m.titulo,
                descricao=m.descricao,
                ordem=m.ordem,
                aulas=[
                    AulaResumoOut(
                        id=a.id,
                        titulo=a.titulo,
                        duracao_minutos=a.duracao_minutos,
                        ordem=a.ordem,
                        concluida=a.concluida,
                    )
                    for a in m.aulas
                ],
            )
            for m in dto.modulos
        ],
    )


@router.get("/aulas/{aula_id}", response_model=AulaDetalheOut)
async def obter_aula(
    aula_id: UUID,
    user: Usuario = Depends(get_current_user),
    use_case: ObterAula = Depends(get_obter_aula),
) -> AulaDetalheOut:
    try:
        dto = await use_case.execute(aula_id, user.id)
    except AulaNaoEncontrada as exc:
        raise AppException("AULA_NOT_FOUND", str(exc), 404) from exc
    except (ModuloNaoEncontrado, TrilhaNaoEncontrada) as exc:
        raise AppException("INTERNAL_ERROR", str(exc), 500) from exc
    return AulaDetalheOut(
        id=dto.id,
        modulo_id=dto.modulo_id,
        titulo=dto.titulo,
        descricao=dto.descricao,
        drive_file_id=dto.drive_file_id,
        duracao_minutos=dto.duracao_minutos,
        concluida=dto.concluida,
        trilha=TrilhaResumoOut(id=dto.trilha.id, titulo=dto.trilha.titulo),
        proxima_aula=(
            AulaResumoOut(
                id=dto.proxima_aula.id,
                titulo=dto.proxima_aula.titulo,
                duracao_minutos=dto.proxima_aula.duracao_minutos,
                ordem=dto.proxima_aula.ordem,
                concluida=dto.proxima_aula.concluida,
            )
            if dto.proxima_aula
            else None
        ),
    )


@router.post(
    "/aulas/{aula_id}/concluir",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def marcar_concluida(
    aula_id: UUID,
    user: Usuario = Depends(get_current_user),
    use_case: MarcarConcluida = Depends(get_marcar_concluida),
) -> None:
    try:
        await use_case.execute(aula_id, user.id)
    except AulaNaoEncontrada as exc:
        raise AppException("AULA_NOT_FOUND", str(exc), 404) from exc


@router.delete(
    "/aulas/{aula_id}/concluir",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def desmarcar_concluida(
    aula_id: UUID,
    user: Usuario = Depends(get_current_user),
    use_case: DesmarcarConcluida = Depends(get_desmarcar_concluida),
) -> None:
    await use_case.execute(aula_id, user.id)
