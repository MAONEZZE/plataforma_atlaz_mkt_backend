from datetime import date

from app.domain.metrics_module.metrics_validator import normalize_to_monday, within_edit_window


def test_normalize_monday_stays_monday() -> None:
    d = date(2026, 5, 4)  # Monday
    assert normalize_to_monday(d) == date(2026, 5, 4)


def test_normalize_wednesday_to_monday() -> None:
    d = date(2026, 5, 6)  # Wednesday
    assert normalize_to_monday(d) == date(2026, 5, 4)


def test_normalize_sunday_to_monday() -> None:
    d = date(2026, 5, 10)  # Sunday
    assert normalize_to_monday(d) == date(2026, 5, 4)


def test_within_window_same_week() -> None:
    week = date(2026, 5, 4)
    today = date(2026, 5, 7)
    assert within_edit_window(week, today) is True


def test_within_window_exactly_28_days() -> None:
    week = date(2026, 4, 13)
    today = date(2026, 5, 11)  # 28 days later
    assert (today - week).days == 28
    assert within_edit_window(week, today) is True


def test_outside_window_29_days() -> None:
    week = date(2026, 4, 12)
    today = date(2026, 5, 11)  # 29 days later
    assert within_edit_window(week, today) is False


def test_outside_window_future_week() -> None:
    week = date(2026, 5, 18)
    today = date(2026, 5, 14)
    assert within_edit_window(week, today) is False
