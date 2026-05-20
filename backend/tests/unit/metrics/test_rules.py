from datetime import date
import pytest
from app.contexts.metricas.domain.rules import normalize_to_monday, dentro_janela_edicao


def test_normalize_monday_stays_monday() -> None:
    d = date(2026, 5, 4)  # Monday
    assert normalize_to_monday(d) == date(2026, 5, 4)


def test_normalize_wednesday_to_monday() -> None:
    d = date(2026, 5, 6)  # Wednesday
    assert normalize_to_monday(d) == date(2026, 5, 4)


def test_normalize_sunday_to_monday() -> None:
    d = date(2026, 5, 10)  # Sunday
    assert normalize_to_monday(d) == date(2026, 5, 4)


def test_dentro_janela_same_week() -> None:
    semana = date(2026, 5, 4)
    today = date(2026, 5, 7)
    assert dentro_janela_edicao(semana, today) is True


def test_dentro_janela_exactly_28_days() -> None:
    semana = date(2026, 4, 13)
    today = date(2026, 5, 11)  # 28 days later
    assert (today - semana).days == 28
    assert dentro_janela_edicao(semana, today) is True


def test_fora_janela_29_days() -> None:
    semana = date(2026, 4, 12)
    today = date(2026, 5, 11)  # 29 days later
    assert dentro_janela_edicao(semana, today) is False


def test_fora_janela_future_semana() -> None:
    semana = date(2026, 5, 18)
    today = date(2026, 5, 14)
    assert dentro_janela_edicao(semana, today) is False
