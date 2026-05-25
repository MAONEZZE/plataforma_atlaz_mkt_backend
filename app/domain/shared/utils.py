from datetime import date, datetime
from zoneinfo import ZoneInfo

_SP_TZ = ZoneInfo("America/Sao_Paulo")


def now_sp() -> datetime:
    return datetime.now(_SP_TZ).replace(tzinfo=None)


def today_sp() -> date:
    return datetime.now(_SP_TZ).date()
