from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from app.contexts.usuarios.application.dtos import AtualizarMeInput, UploadFotoInput
from app.contexts.usuarios.application.use_cases.atualizar_me import AtualizarMe
from app.contexts.usuarios.application.use_cases.obter_me import ObterMe
from app.contexts.usuarios.application.use_cases.upload_foto import UploadFoto
from app.contexts.usuarios.domain.entities import Usuario
from app.contexts.usuarios.domain.exceptions import FotoInvalida, UsuarioNaoEncontrado
from app.shared.domain.exceptions import DomainError

_NOW = datetime(2024, 1, 1, tzinfo=UTC)

# ── Fixtures ──────────────────────────────────────────────────────────────────


def _make_user(user_id: UUID | None = None) -> Usuario:
    return Usuario(
        id=user_id or uuid4(),
        nome="Ana",
        email="ana@test.com",
        telefone=None,
        linkedin_url=None,
        instagram_username=None,
        foto_url=None,
        role="cliente",
        inativo=False,
        criado_em=_NOW,
        atualizado_em=_NOW,
    )


def _repo(user: Usuario | None = None) -> AsyncMock:
    mock = AsyncMock()
    mock.por_id.return_value = user
    mock.atualizar.side_effect = lambda u: u
    return mock


# ── ObterMe ───────────────────────────────────────────────────────────────────


async def test_obter_me_returns_user() -> None:
    user = _make_user()
    uc = ObterMe(repo=_repo(user))
    result = await uc.execute(user.id)
    assert result == user


async def test_obter_me_not_found_raises() -> None:
    uc = ObterMe(repo=_repo(None))
    with pytest.raises(UsuarioNaoEncontrado):
        await uc.execute(uuid4())


# ── AtualizarMe ───────────────────────────────────────────────────────────────


async def test_atualizar_me_updates_nome() -> None:
    user = _make_user()
    uc = AtualizarMe(repo=_repo(user))
    inp = AtualizarMeInput(
        nome="Beatriz", telefone=None, linkedin_url=None, instagram_username=None
    )
    result = await uc.execute(user.id, inp)
    assert result.nome == "Beatriz"


async def test_atualizar_me_updates_telefone() -> None:
    user = _make_user()
    uc = AtualizarMe(repo=_repo(user))
    inp = AtualizarMeInput(
        nome=None, telefone="+5511999999999", linkedin_url=None, instagram_username=None
    )
    result = await uc.execute(user.id, inp)
    assert result.telefone == "+5511999999999"


async def test_atualizar_me_invalid_telefone_raises() -> None:
    user = _make_user()
    uc = AtualizarMe(repo=_repo(user))
    inp = AtualizarMeInput(nome=None, telefone="abc", linkedin_url=None, instagram_username=None)
    with pytest.raises(DomainError):
        await uc.execute(user.id, inp)


async def test_atualizar_me_invalid_linkedin_raises() -> None:
    user = _make_user()
    uc = AtualizarMe(repo=_repo(user))
    inp = AtualizarMeInput(
        nome=None, telefone=None, linkedin_url="https://twitter.com/x", instagram_username=None
    )
    with pytest.raises(DomainError):
        await uc.execute(user.id, inp)


async def test_atualizar_me_valid_linkedin() -> None:
    user = _make_user()
    uc = AtualizarMe(repo=_repo(user))
    inp = AtualizarMeInput(
        nome=None,
        telefone=None,
        linkedin_url="https://linkedin.com/in/ana",
        instagram_username=None,
    )
    result = await uc.execute(user.id, inp)
    assert result.linkedin_url == "https://linkedin.com/in/ana"


async def test_atualizar_me_invalid_instagram_raises() -> None:
    user = _make_user()
    uc = AtualizarMe(repo=_repo(user))
    inp = AtualizarMeInput(
        nome=None, telefone=None, linkedin_url=None, instagram_username="@invalid!"
    )
    with pytest.raises(DomainError):
        await uc.execute(user.id, inp)


async def test_atualizar_me_valid_instagram() -> None:
    user = _make_user()
    uc = AtualizarMe(repo=_repo(user))
    inp = AtualizarMeInput(
        nome=None, telefone=None, linkedin_url=None, instagram_username="ana.silva_99"
    )
    result = await uc.execute(user.id, inp)
    assert result.instagram_username == "ana.silva_99"


async def test_atualizar_me_not_found_raises() -> None:
    uc = AtualizarMe(repo=_repo(None))
    inp = AtualizarMeInput(nome="X", telefone=None, linkedin_url=None, instagram_username=None)
    with pytest.raises(UsuarioNaoEncontrado):
        await uc.execute(uuid4(), inp)


# ── UploadFoto ────────────────────────────────────────────────────────────────

_JPEG_BYTES = b"\xff\xd8\xff" + b"\x00" * 10
_PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 10
_WEBP_BYTES = b"RIFF\x00\x00\x00\x00WEBP" + b"\x00" * 10
_FAKE_BYTES = b"FAKEFAKEFAKE"


def _storage(url: str = "https://cdn.example.com/foto.jpg") -> MagicMock:
    mock = MagicMock()
    mock.upload.return_value = url
    return mock


async def test_upload_foto_jpeg_ok() -> None:
    user = _make_user()
    uc = UploadFoto(repo=_repo(user), storage=_storage())
    inp = UploadFotoInput(usuario_id=user.id, content_type="image/jpeg", data=_JPEG_BYTES)
    result = await uc.execute(inp)
    assert result.foto_url.startswith("https://")


async def test_upload_foto_png_ok() -> None:
    user = _make_user()
    uc = UploadFoto(repo=_repo(user), storage=_storage("https://cdn.example.com/foto.png"))
    inp = UploadFotoInput(usuario_id=user.id, content_type="image/png", data=_PNG_BYTES)
    result = await uc.execute(inp)
    assert result.foto_url


async def test_upload_foto_webp_ok() -> None:
    user = _make_user()
    uc = UploadFoto(repo=_repo(user), storage=_storage())
    inp = UploadFotoInput(usuario_id=user.id, content_type="image/webp", data=_WEBP_BYTES)
    result = await uc.execute(inp)
    assert result.foto_url


async def test_upload_foto_invalid_content_type_raises() -> None:
    user = _make_user()
    uc = UploadFoto(repo=_repo(user), storage=_storage())
    inp = UploadFotoInput(usuario_id=user.id, content_type="application/pdf", data=_JPEG_BYTES)
    with pytest.raises(FotoInvalida):
        await uc.execute(inp)


async def test_upload_foto_too_large_raises() -> None:
    user = _make_user()
    uc = UploadFoto(repo=_repo(user), storage=_storage())
    big = b"\xff\xd8\xff" + b"\x00" * (5 * 1024 * 1024 + 1)
    inp = UploadFotoInput(usuario_id=user.id, content_type="image/jpeg", data=big)
    with pytest.raises(FotoInvalida):
        await uc.execute(inp)


async def test_upload_foto_wrong_magic_bytes_raises() -> None:
    user = _make_user()
    uc = UploadFoto(repo=_repo(user), storage=_storage())
    inp = UploadFotoInput(usuario_id=user.id, content_type="image/jpeg", data=_FAKE_BYTES)
    with pytest.raises(FotoInvalida):
        await uc.execute(inp)


async def test_upload_foto_user_not_found_raises() -> None:
    uc = UploadFoto(repo=_repo(None), storage=_storage())
    inp = UploadFotoInput(usuario_id=uuid4(), content_type="image/jpeg", data=_JPEG_BYTES)
    with pytest.raises(UsuarioNaoEncontrado):
        await uc.execute(inp)
