from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.contexts.auth.domain.entities import Usuario as AuthUsuario
from app.contexts.usuarios.application.dtos import AtualizarMeInput, UploadFotoInput
from app.contexts.usuarios.application.use_cases.atualizar_me import AtualizarMe
from app.contexts.usuarios.application.use_cases.obter_me import ObterMe
from app.contexts.usuarios.application.use_cases.upload_foto import UploadFoto
from app.contexts.usuarios.domain.exceptions import FotoInvalida, UsuarioNaoEncontrado
from app.contexts.usuarios.infrastructure.repositories import SqlAlchemyUsuarioRepository
from app.contexts.usuarios.infrastructure.supabase_storage_gateway import SupabaseStorageGateway
from app.contexts.usuarios.presentation.schemas import (
    FotoUrlResponse,
    PatchMeBody,
    UsuarioResponse,
)
from app.core.db import get_session
from app.core.deps import get_current_user
from app.core.exceptions import AppException
from app.shared.domain.exceptions import DomainError
from app.shared.infrastructure.supabase_client import create_supabase_admin_client

router = APIRouter(prefix="/me", tags=["me"])


def _obter_me(session: AsyncSession = Depends(get_session)) -> ObterMe:
    return ObterMe(repo=SqlAlchemyUsuarioRepository(session))


def _atualizar_me(session: AsyncSession = Depends(get_session)) -> AtualizarMe:
    return AtualizarMe(repo=SqlAlchemyUsuarioRepository(session))


def _upload_foto(session: AsyncSession = Depends(get_session)) -> UploadFoto:
    client = create_supabase_admin_client()
    return UploadFoto(
        repo=SqlAlchemyUsuarioRepository(session),
        storage=SupabaseStorageGateway(client),
    )


@router.get("", response_model=UsuarioResponse)
async def get_me(
    current_user: AuthUsuario = Depends(get_current_user),
    use_case: ObterMe = Depends(_obter_me),
) -> UsuarioResponse:
    try:
        usuario = await use_case.execute(current_user.id)
    except UsuarioNaoEncontrado as exc:
        raise AppException("RESOURCE_NOT_FOUND", "Usuário não encontrado.", 404) from exc
    return UsuarioResponse(
        id=usuario.id,
        nome=usuario.nome,
        email=usuario.email,
        telefone=usuario.telefone,
        linkedin_url=usuario.linkedin_url,
        instagram_username=usuario.instagram_username,
        descricao=usuario.descricao,
        foto_url=usuario.foto_url,
        role=usuario.role,
        criado_em=usuario.criado_em,
    )


@router.patch("", response_model=UsuarioResponse)
async def patch_me(
    body: PatchMeBody,
    current_user: AuthUsuario = Depends(get_current_user),
    use_case: AtualizarMe = Depends(_atualizar_me),
) -> UsuarioResponse:
    inp = AtualizarMeInput(
        nome=body.nome,
        telefone=body.telefone,
        linkedin_url=body.linkedin_url,
        instagram_username=body.instagram_username,
        descricao=body.descricao,
    )
    try:
        usuario = await use_case.execute(current_user.id, inp)
    except UsuarioNaoEncontrado as exc:
        raise AppException("RESOURCE_NOT_FOUND", "Usuário não encontrado.", 404) from exc
    except DomainError as exc:
        raise AppException("VALIDATION_ERROR", str(exc), 400) from exc
    return UsuarioResponse(
        id=usuario.id,
        nome=usuario.nome,
        email=usuario.email,
        telefone=usuario.telefone,
        linkedin_url=usuario.linkedin_url,
        instagram_username=usuario.instagram_username,
        descricao=usuario.descricao,
        foto_url=usuario.foto_url,
        role=usuario.role,
        criado_em=usuario.criado_em,
    )


@router.post("/foto", response_model=FotoUrlResponse)
async def post_foto(
    foto: UploadFile = File(...),
    current_user: AuthUsuario = Depends(get_current_user),
    use_case: UploadFoto = Depends(_upload_foto),
) -> FotoUrlResponse:
    data = await foto.read()
    inp = UploadFotoInput(
        usuario_id=current_user.id,
        content_type=foto.content_type or "",
        data=data,
    )
    try:
        result = await use_case.execute(inp)
    except FotoInvalida as exc:
        raise AppException("VALIDATION_ERROR", str(exc), 400) from exc
    except UsuarioNaoEncontrado as exc:
        raise AppException("RESOURCE_NOT_FOUND", "Usuário não encontrado.", 404) from exc
    return FotoUrlResponse(foto_url=result.foto_url)
