from datetime import UTC, date, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from app.domain.event_module.event_exceptions import EventNotFound
from app.domain.event_module.event_model import EventDate
from app.domain.user_module.user_exceptions import InvalidPhoto
from app.services.event_module.create_event import CreateEvent
from app.services.event_module.delete_event import DeleteEvent
from app.services.event_module.delete_events_by_year import DeleteEventsByYear
from app.services.event_module.list_client_events import ListClientEvents
from app.services.event_module.list_events import ListEvents
from app.services.event_module.update_event import UpdateEvent
from app.services.event_module.upload_event_image import (
    UploadEventImage,
    UploadEventImageInput,
)

NOW = datetime.now(tz=UTC)


def _event(
    client_id: UUID | None = None,
    title: str = "Live event",
    event_date: date = date(2026, 1, 1),
) -> EventDate:
    return EventDate(
        id=uuid4(),
        client_id=client_id,
        title=title,
        date=event_date,
        description=None,
        image_url=None,
        created_at=NOW,
        updated_at=NOW,
    )


def _repo(**kwargs: object) -> AsyncMock:
    repo = AsyncMock()
    for attr, val in kwargs.items():
        if isinstance(val, Exception):
            getattr(repo, attr).side_effect = val
        else:
            getattr(repo, attr).return_value = val
    return repo


# ── CreateEvent ───────────────────────────────────────────────────────────────


async def test_create_event_general() -> None:
    event = _event()
    repo = _repo(create=event)
    result = await CreateEvent(repo).execute(title="Live event", event_date=date(2026, 1, 1))
    assert result.title == "Live event"
    created = repo.create.call_args.args[0]
    assert created.client_id is None


async def test_create_event_particular() -> None:
    client_id = uuid4()
    event = _event(client_id=client_id)
    repo = _repo(create=event)
    await CreateEvent(repo).execute(
        title="1:1", event_date=date(2026, 1, 1), client_id=client_id
    )
    created = repo.create.call_args.args[0]
    assert created.client_id == client_id


# ── UpdateEvent ───────────────────────────────────────────────────────────────


async def test_update_event_happy_path() -> None:
    event = _event(title="old")
    updated = _event(title="new")
    repo = _repo(get_by_id=event, update=updated)
    result = await UpdateEvent(repo).execute(event_id=event.id, title="new")
    assert result.title == "new"


async def test_update_event_not_found() -> None:
    repo = _repo(get_by_id=None)
    with pytest.raises(EventNotFound):
        await UpdateEvent(repo).execute(event_id=uuid4(), title="x")


async def test_update_event_keeps_fields_when_omitted() -> None:
    event = _event(title="keep me", event_date=date(2026, 5, 5))
    repo = _repo(get_by_id=event, update=event)
    await UpdateEvent(repo).execute(event_id=event.id, description="new desc")
    saved = repo.update.call_args.args[0]
    assert saved.title == "keep me"
    assert saved.date == date(2026, 5, 5)


# ── DeleteEvent ───────────────────────────────────────────────────────────────


async def test_delete_event_happy_path() -> None:
    event = _event()
    repo = _repo(get_by_id=event, delete=None)
    await DeleteEvent(repo).execute(event.id)
    repo.delete.assert_called_once_with(event.id)


async def test_delete_event_not_found() -> None:
    repo = _repo(get_by_id=None)
    with pytest.raises(EventNotFound):
        await DeleteEvent(repo).execute(uuid4())


# ── DeleteEventsByYear ────────────────────────────────────────────────────────


async def test_delete_events_by_year_forwards_year_and_scope() -> None:
    repo = _repo(delete_by_year=4)
    deleted = await DeleteEventsByYear(repo).execute(year=2026, scope="general")
    assert deleted == 4
    repo.delete_by_year.assert_awaited_once_with(year=2026, scope="general")


# ── ListEvents (admin) ────────────────────────────────────────────────────────


async def test_list_events_forwards_pagination() -> None:
    repo = _repo(list_for_admin=([_event(), _event()], 2))
    items, total = await ListEvents(repo).execute(page=2, page_size=10)
    assert len(items) == 2
    assert total == 2
    repo.list_for_admin.assert_awaited_once_with(page=2, page_size=10)


# ── ListClientEvents ──────────────────────────────────────────────────────────


async def test_list_client_events_forwards_client_id() -> None:
    client_id = uuid4()
    repo = _repo(list_for_client=([_event(client_id=client_id)], 1))
    items, total = await ListClientEvents(repo).execute(
        client_id=client_id, page=1, page_size=50
    )
    assert total == 1
    repo.list_for_client.assert_awaited_once_with(
        client_id=client_id, page=1, page_size=50
    )


# ── UploadEventImage ──────────────────────────────────────────────────────────

_JPEG_BYTES = b"\xff\xd8\xff" + b"\x00" * 10


def _storage(url: str = "https://cdn.example.com/event.jpg") -> MagicMock:
    mock = AsyncMock()
    mock.upload.return_value = url
    return mock


async def test_upload_event_image_ok() -> None:
    event = _event()
    repo = _repo(get_by_id=event, update=event)
    uc = UploadEventImage(repo=repo, storage=_storage())
    inp = UploadEventImageInput(event_id=event.id, content_type="image/jpeg", data=_JPEG_BYTES)
    result = await uc.execute(inp)
    assert result.image_url.startswith("https://")


async def test_upload_event_image_not_found() -> None:
    repo = _repo(get_by_id=None)
    uc = UploadEventImage(repo=repo, storage=_storage())
    inp = UploadEventImageInput(event_id=uuid4(), content_type="image/jpeg", data=_JPEG_BYTES)
    with pytest.raises(EventNotFound):
        await uc.execute(inp)


async def test_upload_event_image_invalid_content_type() -> None:
    event = _event()
    repo = _repo(get_by_id=event)
    uc = UploadEventImage(repo=repo, storage=_storage())
    inp = UploadEventImageInput(event_id=event.id, content_type="application/pdf", data=_JPEG_BYTES)
    with pytest.raises(InvalidPhoto):
        await uc.execute(inp)
