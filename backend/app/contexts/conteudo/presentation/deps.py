from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.contexts.conteudo.application.use_cases.aulas.crud_admin import (
    AtualizarAula,
    CriarAula,
    RemoverAula,
    ReordenarAulas,
)
from app.contexts.conteudo.application.use_cases.aulas.desmarcar import DesmarcarConcluida
from app.contexts.conteudo.application.use_cases.aulas.marcar_concluida import MarcarConcluida
from app.contexts.conteudo.application.use_cases.aulas.obter import ObterAula
from app.contexts.conteudo.application.use_cases.comentarios.apagar import ApagarComentario
from app.contexts.conteudo.application.use_cases.comentarios.criar import CriarComentario
from app.contexts.conteudo.application.use_cases.comentarios.editar import EditarComentario
from app.contexts.conteudo.application.use_cases.comentarios.listar import ListarComentarios
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
from app.contexts.conteudo.application.use_cases.trilhas.listar_com_progresso import (
    ListarTrilhasComProgresso,
)
from app.contexts.conteudo.application.use_cases.trilhas.obter_com_modulos import (
    ObterTrilhaComModulos,
)
from app.contexts.conteudo.infrastructure.repositories import (
    SqlAlchemyAlunoAulaRepository,
    SqlAlchemyAulaRepository,
    SqlAlchemyComentarioRepository,
    SqlAlchemyModuloRepository,
    SqlAlchemyTrilhaRepository,
)
from app.core.db import get_session


def _repos(session: AsyncSession) -> tuple[
    SqlAlchemyTrilhaRepository,
    SqlAlchemyModuloRepository,
    SqlAlchemyAulaRepository,
    SqlAlchemyAlunoAulaRepository,
    SqlAlchemyComentarioRepository,
]:
    return (
        SqlAlchemyTrilhaRepository(session),
        SqlAlchemyModuloRepository(session),
        SqlAlchemyAulaRepository(session),
        SqlAlchemyAlunoAulaRepository(session),
        SqlAlchemyComentarioRepository(session),
    )


def get_listar_trilhas(session: AsyncSession = Depends(get_session)) -> ListarTrilhasComProgresso:
    t, m, a, aa, _ = _repos(session)
    return ListarTrilhasComProgresso(t, m, a, aa)


def get_obter_trilha(session: AsyncSession = Depends(get_session)) -> ObterTrilhaComModulos:
    t, m, a, aa, _ = _repos(session)
    return ObterTrilhaComModulos(t, m, a, aa)


def get_criar_trilha(session: AsyncSession = Depends(get_session)) -> CriarTrilha:
    t, _, _, _, _ = _repos(session)
    return CriarTrilha(t)


def get_atualizar_trilha(session: AsyncSession = Depends(get_session)) -> AtualizarTrilha:
    t, _, _, _, _ = _repos(session)
    return AtualizarTrilha(t)


def get_remover_trilha(session: AsyncSession = Depends(get_session)) -> RemoverTrilha:
    t, _, _, _, _ = _repos(session)
    return RemoverTrilha(t)


def get_reordenar_trilhas(session: AsyncSession = Depends(get_session)) -> ReordenarTrilhas:
    t, _, _, _, _ = _repos(session)
    return ReordenarTrilhas(t)


def get_criar_modulo(session: AsyncSession = Depends(get_session)) -> CriarModulo:
    _, m, _, _, _ = _repos(session)
    return CriarModulo(m)


def get_atualizar_modulo(session: AsyncSession = Depends(get_session)) -> AtualizarModulo:
    _, m, _, _, _ = _repos(session)
    return AtualizarModulo(m)


def get_remover_modulo(session: AsyncSession = Depends(get_session)) -> RemoverModulo:
    _, m, _, _, _ = _repos(session)
    return RemoverModulo(m)


def get_reordenar_modulos(session: AsyncSession = Depends(get_session)) -> ReordenarModulos:
    _, m, _, _, _ = _repos(session)
    return ReordenarModulos(m)


def get_obter_aula(session: AsyncSession = Depends(get_session)) -> ObterAula:
    t, m, a, aa, _ = _repos(session)
    return ObterAula(a, m, t, aa)


def get_criar_aula(session: AsyncSession = Depends(get_session)) -> CriarAula:
    _, _, a, _, _ = _repos(session)
    return CriarAula(a)


def get_atualizar_aula(session: AsyncSession = Depends(get_session)) -> AtualizarAula:
    _, _, a, _, _ = _repos(session)
    return AtualizarAula(a)


def get_remover_aula(session: AsyncSession = Depends(get_session)) -> RemoverAula:
    _, _, a, _, _ = _repos(session)
    return RemoverAula(a)


def get_reordenar_aulas(session: AsyncSession = Depends(get_session)) -> ReordenarAulas:
    _, _, a, _, _ = _repos(session)
    return ReordenarAulas(a)


def get_marcar_concluida(session: AsyncSession = Depends(get_session)) -> MarcarConcluida:
    _, _, a, aa, _ = _repos(session)
    return MarcarConcluida(a, aa)


def get_desmarcar_concluida(session: AsyncSession = Depends(get_session)) -> DesmarcarConcluida:
    _, _, _, aa, _ = _repos(session)
    return DesmarcarConcluida(aa)


def get_listar_comentarios(session: AsyncSession = Depends(get_session)) -> ListarComentarios:
    _, _, _, _, c = _repos(session)
    return ListarComentarios(c)


def get_criar_comentario(session: AsyncSession = Depends(get_session)) -> CriarComentario:
    _, _, a, _, c = _repos(session)
    return CriarComentario(a, c)


def get_editar_comentario(session: AsyncSession = Depends(get_session)) -> EditarComentario:
    _, _, _, _, c = _repos(session)
    return EditarComentario(c)


def get_apagar_comentario(session: AsyncSession = Depends(get_session)) -> ApagarComentario:
    _, _, _, _, c = _repos(session)
    return ApagarComentario(c)
