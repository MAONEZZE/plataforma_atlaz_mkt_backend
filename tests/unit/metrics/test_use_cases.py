from datetime import UTC, date, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.domain.metrics_module.metrics_exceptions import MetricNotFound, MetricNotOwnedByUser
from app.domain.metrics_module.metrics_model import Metric, MetricEntry
from app.services.metrics_module.create_metric import CreateMetric
from app.services.metrics_module.delete_entry import DeleteEntry
from app.services.metrics_module.delete_metric import DeleteMetric
from app.services.metrics_module.get_sheet import GetSheet
from app.services.metrics_module.list_metrics import ListMetrics
from app.services.metrics_module.update_metric import UpdateMetric
from app.services.metrics_module.upsert_entry import UpsertEntry

NOW = datetime.now(tz=UTC)


def _metric(user_id=None, name="Calls", unit="qtd", order=0) -> Metric:
    return Metric(
        id=uuid4(),
        user_id=user_id or uuid4(),
        name=name,
        unit=unit,
        order=order,
        created_at=NOW,
        updated_at=NOW,
    )


def _entry(metric_id, day: date, value: int) -> MetricEntry:
    return MetricEntry(
        id=uuid4(), metric_id=metric_id, day=day, value=value, created_at=NOW, updated_at=NOW
    )


def _repo(**kwargs: object) -> AsyncMock:
    repo = AsyncMock()
    for attr, val in kwargs.items():
        if isinstance(val, Exception):
            getattr(repo, attr).side_effect = val
        else:
            getattr(repo, attr).return_value = val
    return repo


# ── CreateMetric ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_metric() -> None:
    user_id = uuid4()
    repo = _repo(create_metric=_metric(user_id, "Calls"))
    await CreateMetric(repo).execute(user_id=user_id, name="Calls", unit="qtd")
    created = repo.create_metric.call_args.args[0]
    assert created.user_id == user_id
    assert created.name == "Calls"
    assert created.unit == "qtd"


# ── UpdateMetric ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_update_metric_happy_path() -> None:
    user_id = uuid4()
    metric = _metric(user_id, "old")
    repo = _repo(get_metric_by_id=metric, update_metric=metric)
    await UpdateMetric(repo).execute(
        metric_id=metric.id, requesting_user_id=user_id, name="new", order=3
    )
    saved = repo.update_metric.call_args.args[0]
    assert saved.name == "new"
    assert saved.order == 3


@pytest.mark.asyncio
async def test_update_metric_not_found() -> None:
    repo = _repo(get_metric_by_id=None)
    with pytest.raises(MetricNotFound):
        await UpdateMetric(repo).execute(metric_id=uuid4(), requesting_user_id=uuid4(), name="x")


@pytest.mark.asyncio
async def test_update_metric_not_owned() -> None:
    metric = _metric(uuid4(), "x")
    repo = _repo(get_metric_by_id=metric)
    with pytest.raises(MetricNotOwnedByUser):
        await UpdateMetric(repo).execute(
            metric_id=metric.id, requesting_user_id=uuid4(), name="y"
        )


# ── DeleteMetric ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_delete_metric_happy_path() -> None:
    user_id = uuid4()
    metric = _metric(user_id)
    repo = _repo(get_metric_by_id=metric, delete_metric=None)
    await DeleteMetric(repo).execute(metric_id=metric.id, requesting_user_id=user_id)
    repo.delete_metric.assert_called_once_with(metric.id)


@pytest.mark.asyncio
async def test_delete_metric_not_owned() -> None:
    metric = _metric(uuid4())
    repo = _repo(get_metric_by_id=metric)
    with pytest.raises(MetricNotOwnedByUser):
        await DeleteMetric(repo).execute(metric_id=metric.id, requesting_user_id=uuid4())


@pytest.mark.asyncio
async def test_delete_metric_not_found() -> None:
    repo = _repo(get_metric_by_id=None)
    with pytest.raises(MetricNotFound):
        await DeleteMetric(repo).execute(metric_id=uuid4(), requesting_user_id=uuid4())


# ── ListMetrics ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_metrics() -> None:
    user_id = uuid4()
    repo = _repo(list_metrics=[_metric(user_id, "A"), _metric(user_id, "B")])
    result = await ListMetrics(repo).execute(user_id=user_id)
    assert len(result) == 2


# ── UpsertEntry ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_upsert_entry_happy_path() -> None:
    user_id = uuid4()
    metric = _metric(user_id)
    day = date(2026, 5, 10)
    repo = _repo(get_metric_by_id=metric, upsert_entry=_entry(metric.id, day, 7))
    result = await UpsertEntry(repo).execute(
        metric_id=metric.id, requesting_user_id=user_id, day=day, value=7
    )
    assert result.value == 7
    repo.upsert_entry.assert_called_once_with(metric.id, day, 7)


@pytest.mark.asyncio
async def test_upsert_entry_not_owned() -> None:
    metric = _metric(uuid4())
    repo = _repo(get_metric_by_id=metric)
    with pytest.raises(MetricNotOwnedByUser):
        await UpsertEntry(repo).execute(
            metric_id=metric.id, requesting_user_id=uuid4(), day=date(2026, 5, 1), value=1
        )


@pytest.mark.asyncio
async def test_upsert_entry_metric_not_found() -> None:
    repo = _repo(get_metric_by_id=None)
    with pytest.raises(MetricNotFound):
        await UpsertEntry(repo).execute(
            metric_id=uuid4(), requesting_user_id=uuid4(), day=date(2026, 5, 1), value=1
        )


# ── DeleteEntry ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_delete_entry_happy_path() -> None:
    user_id = uuid4()
    metric = _metric(user_id)
    day = date(2026, 5, 10)
    repo = _repo(get_metric_by_id=metric, delete_entry=None)
    await DeleteEntry(repo).execute(metric_id=metric.id, requesting_user_id=user_id, day=day)
    repo.delete_entry.assert_called_once_with(metric.id, day)


# ── GetSheet ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_sheet_builds_grid_and_days() -> None:
    user_id = uuid4()
    m1 = _metric(user_id, "Calls")
    m2 = _metric(user_id, "Sales")
    entries = [
        _entry(m1.id, date(2026, 5, 3), 5),
        _entry(m1.id, date(2026, 5, 4), 8),
        _entry(m2.id, date(2026, 5, 3), 1),
    ]
    repo = _repo(list_metrics=[m1, m2], list_entries=entries)
    sheet = await GetSheet(repo).execute(user_id=user_id, month="2026-05")

    assert sheet.month == "2026-05"
    assert len(sheet.columns) == 2
    assert len(sheet.days) == 31  # May has 31 days
    assert sheet.entries[str(m1.id)]["2026-05-03"] == 5
    assert sheet.entries[str(m1.id)]["2026-05-04"] == 8
    assert sheet.entries[str(m2.id)]["2026-05-03"] == 1
    args = repo.list_entries.call_args.args
    passed = list(args) + list(repo.list_entries.call_args.kwargs.values())
    assert date(2026, 5, 1) in passed
    assert date(2026, 5, 31) in passed
