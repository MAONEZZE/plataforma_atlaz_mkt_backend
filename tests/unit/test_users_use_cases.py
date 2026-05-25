from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from app.api.controllers.user_module.user_dto.user_dto import UpdateMeInput, UploadPhotoInput
from app.domain.shared.base_exceptions import DomainError
from app.domain.user_module.user_exceptions import InvalidPhoto, UserNotFound
from app.domain.user_module.user_model import User
from app.services.user_module.user_service.get_me_service import GetMe
from app.services.user_module.user_service.update_me_service import UpdateMe
from app.services.user_module.user_service.upload_photo_service import UploadPhoto

_NOW = datetime(2024, 1, 1, tzinfo=UTC)

# ── Fixtures ──────────────────────────────────────────────────────────────────


def _make_user(user_id: UUID | None = None) -> User:
    return User(
        id=user_id or uuid4(),
        name="Ana",
        email="ana@test.com",
        phone=None,
        linkedin_url=None,
        instagram_username=None,
        description=None,
        photo_url=None,
        role="cliente",
        inactive=False,
        created_at=_NOW,
        updated_at=_NOW,
    )


def _repo(user: User | None = None) -> AsyncMock:
    mock = AsyncMock()
    mock.get_by_id.return_value = user
    mock.update.side_effect = lambda u: u
    return mock


# ── GetMe ─────────────────────────────────────────────────────────────────────


async def test_get_me_returns_user() -> None:
    user = _make_user()
    uc = GetMe(repo=_repo(user))
    result = await uc.execute(user.id)
    assert result == user


async def test_get_me_not_found_raises() -> None:
    uc = GetMe(repo=_repo(None))
    with pytest.raises(UserNotFound):
        await uc.execute(uuid4())


# ── UpdateMe ──────────────────────────────────────────────────────────────────


async def test_update_me_updates_name() -> None:
    user = _make_user()
    uc = UpdateMe(repo=_repo(user))
    inp = UpdateMeInput(
        name="Beatriz", phone=None, linkedin_url=None, instagram_username=None
    )
    result = await uc.execute(user.id, inp)
    assert result.name == "Beatriz"


async def test_update_me_updates_phone() -> None:
    user = _make_user()
    uc = UpdateMe(repo=_repo(user))
    inp = UpdateMeInput(
        name=None, phone="+5511999999999", linkedin_url=None, instagram_username=None
    )
    result = await uc.execute(user.id, inp)
    assert result.phone == "+5511999999999"


async def test_update_me_invalid_phone_raises() -> None:
    user = _make_user()
    uc = UpdateMe(repo=_repo(user))
    inp = UpdateMeInput(name=None, phone="abc", linkedin_url=None, instagram_username=None)
    with pytest.raises(DomainError):
        await uc.execute(user.id, inp)


async def test_update_me_invalid_linkedin_raises() -> None:
    user = _make_user()
    uc = UpdateMe(repo=_repo(user))
    inp = UpdateMeInput(
        name=None, phone=None, linkedin_url="https://twitter.com/x", instagram_username=None
    )
    with pytest.raises(DomainError):
        await uc.execute(user.id, inp)


async def test_update_me_valid_linkedin() -> None:
    user = _make_user()
    uc = UpdateMe(repo=_repo(user))
    inp = UpdateMeInput(
        name=None,
        phone=None,
        linkedin_url="https://linkedin.com/in/ana",
        instagram_username=None,
    )
    result = await uc.execute(user.id, inp)
    assert result.linkedin_url == "https://linkedin.com/in/ana"


async def test_update_me_invalid_instagram_raises() -> None:
    user = _make_user()
    uc = UpdateMe(repo=_repo(user))
    inp = UpdateMeInput(
        name=None, phone=None, linkedin_url=None, instagram_username="@invalid!"
    )
    with pytest.raises(DomainError):
        await uc.execute(user.id, inp)


async def test_update_me_valid_instagram() -> None:
    user = _make_user()
    uc = UpdateMe(repo=_repo(user))
    inp = UpdateMeInput(
        name=None, phone=None, linkedin_url=None, instagram_username="ana.silva_99"
    )
    result = await uc.execute(user.id, inp)
    assert result.instagram_username == "ana.silva_99"


async def test_update_me_updates_description() -> None:
    user = _make_user()
    uc = UpdateMe(repo=_repo(user))
    inp = UpdateMeInput(
        name=None, phone=None, linkedin_url=None, instagram_username=None,
        description="Professional trader.",
    )
    result = await uc.execute(user.id, inp)
    assert result.description == "Professional trader."


async def test_update_me_not_found_raises() -> None:
    uc = UpdateMe(repo=_repo(None))
    inp = UpdateMeInput(name="X", phone=None, linkedin_url=None, instagram_username=None, description=None)
    with pytest.raises(UserNotFound):
        await uc.execute(uuid4(), inp)


# ── UploadPhoto ───────────────────────────────────────────────────────────────

_JPEG_BYTES = b"\xff\xd8\xff" + b"\x00" * 10
_PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 10
_WEBP_BYTES = b"RIFF\x00\x00\x00\x00WEBP" + b"\x00" * 10
_FAKE_BYTES = b"FAKEFAKEFAKE"


def _storage(url: str = "https://cdn.example.com/photo.jpg") -> MagicMock:
    mock = MagicMock()
    mock.upload.return_value = url
    return mock


async def test_upload_photo_jpeg_ok() -> None:
    user = _make_user()
    uc = UploadPhoto(repo=_repo(user), storage=_storage())
    inp = UploadPhotoInput(user_id=user.id, content_type="image/jpeg", data=_JPEG_BYTES)
    result = await uc.execute(inp)
    assert result.photo_url.startswith("https://")


async def test_upload_photo_png_ok() -> None:
    user = _make_user()
    uc = UploadPhoto(repo=_repo(user), storage=_storage("https://cdn.example.com/photo.png"))
    inp = UploadPhotoInput(user_id=user.id, content_type="image/png", data=_PNG_BYTES)
    result = await uc.execute(inp)
    assert result.photo_url


async def test_upload_photo_webp_ok() -> None:
    user = _make_user()
    uc = UploadPhoto(repo=_repo(user), storage=_storage())
    inp = UploadPhotoInput(user_id=user.id, content_type="image/webp", data=_WEBP_BYTES)
    result = await uc.execute(inp)
    assert result.photo_url


async def test_upload_photo_invalid_content_type_raises() -> None:
    user = _make_user()
    uc = UploadPhoto(repo=_repo(user), storage=_storage())
    inp = UploadPhotoInput(user_id=user.id, content_type="application/pdf", data=_JPEG_BYTES)
    with pytest.raises(InvalidPhoto):
        await uc.execute(inp)


async def test_upload_photo_too_large_raises() -> None:
    user = _make_user()
    uc = UploadPhoto(repo=_repo(user), storage=_storage())
    big = b"\xff\xd8\xff" + b"\x00" * (5 * 1024 * 1024 + 1)
    inp = UploadPhotoInput(user_id=user.id, content_type="image/jpeg", data=big)
    with pytest.raises(InvalidPhoto):
        await uc.execute(inp)


async def test_upload_photo_wrong_magic_bytes_raises() -> None:
    user = _make_user()
    uc = UploadPhoto(repo=_repo(user), storage=_storage())
    inp = UploadPhotoInput(user_id=user.id, content_type="image/jpeg", data=_FAKE_BYTES)
    with pytest.raises(InvalidPhoto):
        await uc.execute(inp)


async def test_upload_photo_user_not_found_raises() -> None:
    uc = UploadPhoto(repo=_repo(None), storage=_storage())
    inp = UploadPhotoInput(user_id=uuid4(), content_type="image/jpeg", data=_JPEG_BYTES)
    with pytest.raises(UserNotFound):
        await uc.execute(inp)
