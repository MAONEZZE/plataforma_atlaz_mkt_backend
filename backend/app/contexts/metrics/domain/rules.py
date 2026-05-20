from datetime import date, timedelta


def normalize_to_monday(d: date) -> date:
    return d - timedelta(days=d.weekday())


def within_edit_window(week_start: date, today: date) -> bool:
    return (today - week_start).days <= 28 and week_start <= today
