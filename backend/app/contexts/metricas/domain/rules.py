from datetime import date, timedelta


def normalize_to_monday(d: date) -> date:
    return d - timedelta(days=d.weekday())


def dentro_janela_edicao(semana_inicio: date, today: date) -> bool:
    return (today - semana_inicio).days <= 28 and semana_inicio <= today
