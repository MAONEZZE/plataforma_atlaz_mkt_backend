from dataclasses import replace
from datetime import UTC, date, datetime
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest

from app.api.controllers.metrics_module.metrics_dto.metrics_dto import (
    AdminConsolidatedDTO,
    DashboardSeriesDTO,
    DashboardSummaryDTO,
    MetricDTO,
)
from app.domain.metrics_module.metrics_exceptions import (
    DuplicateMetric,
    FutureWeekNotAllowed,
    MetricNotFound,
    MetricNotOwnedByUser,
    MetricOutOfWindow,
)
from app.domain.metrics_module.metrics_model import UserMonthlyMetrics, WeeklyMetric
from app.services.metrics_module.metrics_service.create_metric import CreateMetric
from app.services.metrics_module.metrics_service.get_admin_consolidated import GetAdminConsolidated
from app.services.metrics_module.metrics_service.get_dashboard_series import GetDashboardSeries
from app.services.metrics_module.metrics_service.get_dashboard_summary import GetDashboardSummary
from app.services.metrics_module.metrics_service.list_metrics import ListMetrics
from app.services.metrics_module.metrics_service.update_metric import UpdateMetric

TODAY = date(2026, 5, 14)  # Wednesday
MONDAY = date(2026, 5, 11)  # Monday of current week


def _make_metric(
    user_id: UUID | None = None,
    week_start: date = MONDAY,
) -> WeeklyMetric:
    now = datetime.now(tz=UTC)
    return WeeklyMetric(
        id=uuid4(),
        user_id=user_id or uuid4(),
        week_start=week_start,
        calls_scheduled=10,
        calls_made=8,
        meetings_scheduled=3,
        referrals=1,
        created_at=now,
        updated_at=now,
    )


def _mock_repo(**kwargs: object) -> AsyncMock:
    repo = AsyncMock()
    for attr, val in kwargs.items():
        if isinstance(val, Exception):
            getattr(repo, attr).side_effect = val
        else:
            getattr(repo, attr).return_value = val
    return repo


# ── CreateMetric ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_metric_happy_path() -> None:
    user_id = uuid4()
    metric = _make_metric(user_id=user_id)
    repo = _mock_repo(get_by_user_and_week=None, create=metric)
    uc = CreateMetric(repo)
    result = await uc.execute(
        user_id=user_id,
        week_start=MONDAY,
        calls_scheduled=10,
        calls_made=8,
        meetings_scheduled=3,
        referrals=1,
        is_admin=False,
        today=TODAY,
    )
    assert isinstance(result, MetricDTO)
    assert result.week_start == MONDAY


@pytest.mark.asyncio
async def test_create_metric_normalizes_to_monday() -> None:
    user_id = uuid4()
    wednesday = date(2026, 5, 13)  # Wednesday → should normalize to Monday May 11
    metric = _make_metric(user_id=user_id, week_start=MONDAY)
    repo = _mock_repo(get_by_user_and_week=None, create=metric)
    uc = CreateMetric(repo)
    result = await uc.execute(
        user_id=user_id,
        week_start=wednesday,
        calls_scheduled=0,
        calls_made=0,
        meetings_scheduled=0,
        referrals=0,
        is_admin=False,
        today=TODAY,
    )
    assert result.week_start == MONDAY


@pytest.mark.asyncio
async def test_create_metric_future_week_raises() -> None:
    future = date(2026, 5, 18)  # next Monday
    repo = _mock_repo(get_by_user_and_week=None)
    uc = CreateMetric(repo)
    with pytest.raises(FutureWeekNotAllowed):
        await uc.execute(
            user_id=uuid4(),
            week_start=future,
            calls_scheduled=0,
            calls_made=0,
            meetings_scheduled=0,
            referrals=0,
            is_admin=False,
            today=TODAY,
        )


@pytest.mark.asyncio
async def test_create_metric_outside_window_raises_for_client() -> None:
    old_week = date(2026, 4, 13)  # 31 days before TODAY=May 14 → outside 28-day window
    repo = _mock_repo(get_by_user_and_week=None)
    uc = CreateMetric(repo)
    with pytest.raises(MetricOutOfWindow):
        await uc.execute(
            user_id=uuid4(),
            week_start=old_week,
            calls_scheduled=0,
            calls_made=0,
            meetings_scheduled=0,
            referrals=0,
            is_admin=False,
            today=TODAY,
        )


@pytest.mark.asyncio
async def test_create_metric_outside_window_allowed_for_admin() -> None:
    old_week = date(2026, 1, 5)  # very old, admin can still create
    metric = _make_metric(week_start=old_week)
    repo = _mock_repo(get_by_user_and_week=None, create=metric)
    uc = CreateMetric(repo)
    result = await uc.execute(
        user_id=uuid4(),
        week_start=old_week,
        calls_scheduled=5,
        calls_made=5,
        meetings_scheduled=1,
        referrals=0,
        is_admin=True,
        today=TODAY,
    )
    assert isinstance(result, MetricDTO)


@pytest.mark.asyncio
async def test_create_metric_duplicate_raises() -> None:
    existing = _make_metric()
    repo = _mock_repo(get_by_user_and_week=existing)
    uc = CreateMetric(repo)
    with pytest.raises(DuplicateMetric):
        await uc.execute(
            user_id=existing.user_id,
            week_start=MONDAY,
            calls_scheduled=0,
            calls_made=0,
            meetings_scheduled=0,
            referrals=0,
            is_admin=False,
            today=TODAY,
        )


# ── UpdateMetric ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_update_metric_happy_path() -> None:
    user_id = uuid4()
    metric = _make_metric(user_id=user_id)
    updated = replace(metric, calls_scheduled=20)
    repo = _mock_repo(get_by_id=metric, update=updated)
    uc = UpdateMetric(repo)
    result = await uc.execute(
        metric_id=metric.id,
        requesting_user_id=user_id,
        is_admin=False,
        calls_scheduled=20,
        today=TODAY,
    )
    assert result.calls_scheduled == 20


@pytest.mark.asyncio
async def test_update_metric_not_found_raises() -> None:
    repo = _mock_repo(get_by_id=None)
    uc = UpdateMetric(repo)
    with pytest.raises(MetricNotFound):
        await uc.execute(
            metric_id=uuid4(),
            requesting_user_id=uuid4(),
            is_admin=False,
            today=TODAY,
        )


@pytest.mark.asyncio
async def test_update_metric_wrong_owner_raises() -> None:
    metric = _make_metric()
    repo = _mock_repo(get_by_id=metric)
    uc = UpdateMetric(repo)
    with pytest.raises(MetricNotOwnedByUser):
        await uc.execute(
            metric_id=metric.id,
            requesting_user_id=uuid4(),  # different user
            is_admin=False,
            today=TODAY,
        )


@pytest.mark.asyncio
async def test_update_metric_outside_window_raises_for_client() -> None:
    old_week = date(2026, 4, 12)  # outside 28-day window (33 days from May 14)
    user_id = uuid4()
    metric = _make_metric(user_id=user_id, week_start=old_week)
    repo = _mock_repo(get_by_id=metric)
    uc = UpdateMetric(repo)
    with pytest.raises(MetricOutOfWindow):
        await uc.execute(
            metric_id=metric.id,
            requesting_user_id=user_id,
            is_admin=False,
            today=TODAY,
        )


@pytest.mark.asyncio
async def test_update_metric_outside_window_allowed_for_admin() -> None:
    old_week = date(2026, 1, 5)
    user_id = uuid4()
    metric = _make_metric(user_id=user_id, week_start=old_week)
    updated = replace(metric, calls_scheduled=99)
    repo = _mock_repo(get_by_id=metric, update=updated)
    uc = UpdateMetric(repo)
    result = await uc.execute(
        metric_id=metric.id,
        requesting_user_id=uuid4(),  # admin can edit anyone's
        is_admin=True,
        calls_scheduled=99,
        today=TODAY,
    )
    assert result.calls_scheduled == 99


# ── ListMetrics ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_metrics_returns_paged() -> None:
    user_id = uuid4()
    metrics = [_make_metric(user_id=user_id) for _ in range(3)]
    repo = _mock_repo(list_all=(metrics, 3))
    uc = ListMetrics(repo)
    result = await uc.execute(
        user_id=user_id, month=None, page=1, page_size=20
    )
    assert result.total == 3
    assert len(result.items) == 3
    assert all(isinstance(i, MetricDTO) for i in result.items)


# ── GetDashboardSummary ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_summary_computes_delta() -> None:
    user_id = uuid4()

    async def sum_by_month(uid: UUID, month: str) -> dict[str, int]:
        if month == "2026-05":
            return {"calls_scheduled": 120, "calls_made": 95,
                    "meetings_scheduled": 28, "referrals": 12}
        # prev month 2026-04
        return {"calls_scheduled": 100, "calls_made": 0,
                "meetings_scheduled": 20, "referrals": 0}

    repo = AsyncMock()
    repo.sum_by_month.side_effect = sum_by_month
    uc = GetDashboardSummary(repo)
    result = await uc.execute(user_id=user_id, month="2026-05")

    assert result.month == "2026-05"
    assert result.calls_scheduled.value == 120
    assert result.calls_scheduled.delta_pct == 20.0  # (120-100)/100*100
    # prev=0 → delta_pct=null
    assert result.calls_made.delta_pct is None
    assert result.referrals.delta_pct is None


@pytest.mark.asyncio
async def test_summary_defaults_month_to_current() -> None:
    repo = AsyncMock()
    repo.sum_by_month.return_value = {
        "calls_scheduled": 0,
        "calls_made": 0,
        "meetings_scheduled": 0,
        "referrals": 0,
    }
    uc = GetDashboardSummary(repo)
    result = await uc.execute(user_id=uuid4())
    assert isinstance(result, DashboardSummaryDTO)
    assert repo.sum_by_month.call_count == 2  # current + previous month


# ── GetDashboardSeries ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_series_fills_gaps_with_zeros() -> None:
    user_id = uuid4()
    repo = _mock_repo(get_by_weeks=[])
    uc = GetDashboardSeries(repo)
    result = await uc.execute(
        user_id=user_id, semanas=4, today=date(2026, 5, 14)
    )
    assert isinstance(result, DashboardSeriesDTO)
    assert len(result.series) == 4
    for item in result.series:
        assert item.calls_scheduled == 0
        assert item.calls_made == 0


@pytest.mark.asyncio
async def test_series_correct_length() -> None:
    repo = _mock_repo(get_by_weeks=[])
    uc = GetDashboardSeries(repo)
    result = await uc.execute(
        user_id=uuid4(), semanas=12, today=date(2026, 5, 14)
    )
    assert len(result.series) == 12


@pytest.mark.asyncio
async def test_series_ascending_order() -> None:
    repo = _mock_repo(get_by_weeks=[])
    uc = GetDashboardSeries(repo)
    result = await uc.execute(
        user_id=uuid4(), semanas=4, today=date(2026, 5, 14)
    )
    dates = [s.week for s in result.series]
    assert dates == sorted(dates)


@pytest.mark.asyncio
async def test_series_includes_data_when_available() -> None:
    user_id = uuid4()
    now = datetime.now(tz=UTC)
    # May 11 is in the last 4 weeks of May 14
    week = date(2026, 5, 11)
    metric = WeeklyMetric(
        id=uuid4(), user_id=user_id, week_start=week,
        calls_scheduled=5, calls_made=4,
        meetings_scheduled=2, referrals=1,
        created_at=now, updated_at=now,
    )
    repo = _mock_repo(get_by_weeks=[metric])
    uc = GetDashboardSeries(repo)
    result = await uc.execute(
        user_id=user_id, semanas=4, today=date(2026, 5, 14)
    )
    may11_entry = next(s for s in result.series if s.week == week)
    assert may11_entry.calls_scheduled == 5
    assert may11_entry.referrals == 1


# ── GetAdminConsolidated ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_admin_consolidated_aggregates_correctly() -> None:
    items = [
        UserMonthlyMetrics(
            user_id=uuid4(), name="Alice", photo_url=None,
            calls_scheduled=100, calls_made=80,
            meetings_scheduled=25, referrals=5,
            last_metric_at=date(2026, 5, 4),
        ),
        UserMonthlyMetrics(
            user_id=uuid4(), name="Bob", photo_url=None,
            calls_scheduled=0, calls_made=0,
            meetings_scheduled=0, referrals=0,
            last_metric_at=None,
        ),
    ]
    repo = _mock_repo(list_clients_with_metrics_month=items)
    uc = GetAdminConsolidated(repo)
    result = await uc.execute(month="2026-05", search=None, page=1, page_size=20)

    assert isinstance(result, AdminConsolidatedDTO)
    assert result.aggregates.calls_scheduled_total == 100
    assert result.aggregates.users_with_metric_in_month == 1
    assert result.aggregates.users_without_metric_in_month == 1
    assert result.total == 2


@pytest.mark.asyncio
async def test_admin_consolidated_filters_by_search() -> None:
    items = [
        UserMonthlyMetrics(
            user_id=uuid4(), name="Alice", photo_url=None,
            calls_scheduled=10, calls_made=8,
            meetings_scheduled=2, referrals=1,
            last_metric_at=date(2026, 5, 4),
        ),
        UserMonthlyMetrics(
            user_id=uuid4(), name="Carlos", photo_url=None,
            calls_scheduled=5, calls_made=4,
            meetings_scheduled=1, referrals=0,
            last_metric_at=date(2026, 5, 4),
        ),
    ]
    repo = _mock_repo(list_clients_with_metrics_month=items)
    uc = GetAdminConsolidated(repo)
    result = await uc.execute(month="2026-05", search="ali", page=1, page_size=20)

    assert result.total == 1
    assert result.items[0].name == "Alice"


@pytest.mark.asyncio
async def test_admin_consolidated_paginates() -> None:
    items = [
        UserMonthlyMetrics(
            user_id=uuid4(), name=f"User{i}", photo_url=None,
            calls_scheduled=i, calls_made=0,
            meetings_scheduled=0, referrals=0,
            last_metric_at=None,
        )
        for i in range(25)
    ]
    repo = _mock_repo(list_clients_with_metrics_month=items)
    uc = GetAdminConsolidated(repo)
    result = await uc.execute(month="2026-05", search=None, page=2, page_size=10)

    assert result.total == 25
    assert len(result.items) == 10
    assert result.page == 2
