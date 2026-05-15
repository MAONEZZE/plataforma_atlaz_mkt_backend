from uuid import UUID

from fastapi import APIRouter, Depends
from starlette import status

from app.contexts.auth.domain.entities import Usuario
from app.contexts.conteudo.application.use_cases.aulas.crud_admin import (
    AtualizarAula,
    CriarAula,
    RemoverAula,
    ReordenarAulas,
)
from app.contexts.conteudo.application.use_cases.modulos.crud_admin import (
    AtualizarModulo,
    CriarModulo,
    RemoverModulo,
    ReordenarModulos,
)
from app.contexts.conteudo.application.use_cases.trilhas.crud_admin import (
    AtualizarTrilha,
    CriarTrilha,
    RemoverTrilha,
    ReordenarTrilhas,
)
from app.contexts.conteudo.domain.exceptions import (
    AulaNaoEncontrada,
    DriveUrlInvalida,
    ModuloNaoEncontrado,
    TrilhaNaoEncontrada,
)
from app.contexts.conteudo.presentation.deps import (
    get_atualizar_aula,
    get_atualizar_modulo,
    get_atualizar_trilha,
    get_criar_aula,
    get_criar_modulo,
    get_criar_trilha,
    get_remover_aula,
    get_remover_modulo,
    get_remover_trilha,
    get_reordenar_aulas,
    get_reordenar_modulos,
    get_reordenar_trilhas,
)
from app.contexts.conteudo.presentation.schemas import (
    AtualizarAulaIn,
    AtualizarModuloIn,
    AtualizarTrilhaIn,
    AulaAdminOut,
    CriarAulaIn,
    CriarModuloIn,
    CriarTrilhaIn,
    ModuloAdminOut,
    ReordenarIn,
    TrilhaAdminOut,
)
from app.core.deps import require_admin
from app.core.exceptions import AppException

router = APIRouter(prefix="/admin", tags=["admin-conteudo"])


# ── Trilhas ────────────────────────────────────────────────────────────────────


@router.post("/trilhas", response_model=TrilhaAdminOut, status_code=status.HTTP_201_CREATED)
async def criar_trilha(
    body: CriarTrilhaIn,
    _: Usuario = Depends(require_admin),
    use_case: CriarTrilha = Depends(get_criar_trilha),
) -> TrilhaAdminOut:
    trilha = await use_case.execute(body.titulo, body.descricao, body.capa_url, body.ordem)
    return TrilhaAdminOut(
        id=trilha.id,
        titulo=trilha.titulo,
        descricao=trilha.descricao,
        capa_url=trilha.capa_url,
        ordem=trilha.ordem,
        criado_em=trilha.criado_em,
    )


@router.patch("/trilhas/{trilha_id}", response_model=TrilhaAdminOut)
async def atualizar_trilha(
    trilha_id: UUID,
    body: AtualizarTrilhaIn,
    _: Usuario = Depends(require_admin),
    use_case: AtualizarTrilha = Depends(get_atualizar_trilha),
) -> TrilhaAdminOut:
    try:
        trilha = await use_case.execute(
            trilha_id, body.titulo, body.descricao, body.capa_url, body.ordem
        )
    except TrilhaNaoEncontrada as exc:
        raise AppException("TRILHA_NOT_FOUND", str(exc), 404) from exc
    return TrilhaAdminOut(
        id=trilha.id,
        titulo=trilha.titulo,
        descricao=trilha.descricao,
        capa_url=trilha.capa_url,
        ordem=trilha.ordem,
        criado_em=trilha.criado_em,
    )


@router.delete("/trilhas/{trilha_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remover_trilha(
    trilha_id: UUID,
    _: Usuario = Depends(require_admin),
    use_case: RemoverTrilha = Depends(get_remover_trilha),
) -> None:
    try:
        await use_case.execute(trilha_id)
    except TrilhaNaoEncontrada as exc:
        raise AppException("TRILHA_NOT_FOUND", str(exc), 404) from exc


@router.post("/trilhas/reordenar", status_code=status.HTTP_204_NO_CONTENT)
async def reordenar_trilhas(
    body: ReordenarIn,
    _: Usuario = Depends(require_admin),
    use_case: ReordenarTrilhas = Depends(get_reordenar_trilhas),
) -> None:
    await use_case.execute([(item.id, item.ordem) for item in body.ordem])


# ── Módulos ────────────────────────────────────────────────────────────────────


@router.post("/modulos", response_model=ModuloAdminOut, status_code=status.HTTP_201_CREATED)
async def criar_modulo(
    body: CriarModuloIn,
    _: Usuario = Depends(require_admin),
    use_case: CriarModulo = Depends(get_criar_modulo),
) -> ModuloAdminOut:
    modulo = await use_case.execute(body.trilha_id, body.titulo, body.descricao, body.ordem)
    return ModuloAdminOut(
        id=modulo.id,
        trilha_id=modulo.trilha_id,
        titulo=modulo.titulo,
        descricao=modulo.descricao,
        ordem=modulo.ordem,
    )


@router.patch("/modulos/{modulo_id}", response_model=ModuloAdminOut)
async def atualizar_modulo(
    modulo_id: UUID,
    body: AtualizarModuloIn,
    _: Usuario = Depends(require_admin),
    use_case: AtualizarModulo = Depends(get_atualizar_modulo),
) -> ModuloAdminOut:
    try:
        modulo = await use_case.execute(modulo_id, body.titulo, body.descricao, body.ordem)
    except ModuloNaoEncontrado as exc:
        raise AppException("MODULO_NOT_FOUND", str(exc), 404) from exc
    return ModuloAdminOut(
        id=modulo.id,
        trilha_id=modulo.trilha_id,
        titulo=modulo.titulo,
        descricao=modulo.descricao,
        ordem=modulo.ordem,
    )


@router.delete("/modulos/{modulo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remover_modulo(
    modulo_id: UUID,
    _: Usuario = Depends(require_admin),
    use_case: RemoverModulo = Depends(get_remover_modulo),
) -> None:
    try:
        await use_case.execute(modulo_id)
    except ModuloNaoEncontrado as exc:
        raise AppException("MODULO_NOT_FOUND", str(exc), 404) from exc


@router.post("/modulos/reordenar", status_code=status.HTTP_204_NO_CONTENT)
async def reordenar_modulos(
    body: ReordenarIn,
    _: Usuario = Depends(require_admin),
    use_case: ReordenarModulos = Depends(get_reordenar_modulos),
) -> None:
    await use_case.execute([(item.id, item.ordem) for item in body.ordem])


# ── Aulas ──────────────────────────────────────────────────────────────────────


@router.post("/aulas", response_model=AulaAdminOut, status_code=status.HTTP_201_CREATED)
async def criar_aula(
    body: CriarAulaIn,
    _: Usuario = Depends(require_admin),
    use_case: CriarAula = Depends(get_criar_aula),
) -> AulaAdminOut:
    try:
        aula = await use_case.execute(
            body.modulo_id,
            body.titulo,
            body.descricao,
            body.drive_url,
            body.duracao_minutos,
            body.ordem,
        )
    except DriveUrlInvalida as exc:
        raise AppException("DRIVE_URL_INVALID", str(exc), 400) from exc
    return AulaAdminOut(
        id=aula.id,
        modulo_id=aula.modulo_id,
        titulo=aula.titulo,
        descricao=aula.descricao,
        drive_file_id=aula.drive_file_id,
        duracao_minutos=aula.duracao_minutos,
        ordem=aula.ordem,
        criado_em=aula.criado_em,
    )


@router.patch("/aulas/{aula_id}", response_model=AulaAdminOut)
async def atualizar_aula(
    aula_id: UUID,
    body: AtualizarAulaIn,
    _: Usuario = Depends(require_admin),
    use_case: AtualizarAula = Depends(get_atualizar_aula),
) -> AulaAdminOut:
    try:
        aula = await use_case.execute(
            aula_id,
            body.titulo,
            body.descricao,
            body.drive_url,
            body.duracao_minutos,
            body.ordem,
        )
    except AulaNaoEncontrada as exc:
        raise AppException("AULA_NOT_FOUND", str(exc), 404) from exc
    except DriveUrlInvalida as exc:
        raise AppException("DRIVE_URL_INVALID", str(exc), 400) from exc
    return AulaAdminOut(
        id=aula.id,
        modulo_id=aula.modulo_id,
        titulo=aula.titulo,
        descricao=aula.descricao,
        drive_file_id=aula.drive_file_id,
        duracao_minutos=aula.duracao_minutos,
        ordem=aula.ordem,
        criado_em=aula.criado_em,
    )


@router.delete("/aulas/{aula_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remover_aula(
    aula_id: UUID,
    _: Usuario = Depends(require_admin),
    use_case: RemoverAula = Depends(get_remover_aula),
) -> None:
    try:
        await use_case.execute(aula_id)
    except AulaNaoEncontrada as exc:
        raise AppException("AULA_NOT_FOUND", str(exc), 404) from exc


@router.post("/aulas/reordenar", status_code=status.HTTP_204_NO_CONTENT)
async def reordenar_aulas(
    body: ReordenarIn,
    _: Usuario = Depends(require_admin),
    use_case: ReordenarAulas = Depends(get_reordenar_aulas),
) -> None:
    await use_case.execute([(item.id, item.ordem) for item in body.ordem])
