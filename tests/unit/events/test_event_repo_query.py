"""Unit tests for SqlAlchemyEventRepository query construction.

No real database is available in this suite, so these tests capture the
statements passed to session.execute() and inspect their compiled SQL with
literal binds, instead of asserting on returned rows.
"""

from datetime import date
from typing import Any
from uuid import uuid4

from app.database.event_module.event_repo import SqlAlchemyEventRepository


class _FakeResult:
    def __init__(self, rowcount: int = 0) -> None:
        self.rowcount = rowcount

    def all(self) -> list[Any]:
        return []

    def scalars(self) -> list[Any]:
        return []

    def scalar_one(self) -> int:
        return 0


class _FakeSession:
    def __init__(self, rowcount: int = 0) -> None:
        self.statements: list[Any] = []
        self._rowcount = rowcount

    async def execute(self, stmt: Any) -> _FakeResult:
        self.statements.append(stmt)
        return _FakeResult(rowcount=self._rowcount)


def _compiled(stmt: Any) -> str:
    return str(stmt.compile(compile_kwargs={"literal_binds": True}))


async def test_list_for_admin_orders_by_date_with_id_tiebreak() -> None:
    session = _FakeSession()
    repo = SqlAlchemyEventRepository(session)  # type: ignore[arg-type]

    await repo.list_for_admin(page=1, page_size=50)

    page_sql = _compiled(session.statements[0])
    order_clause = page_sql.split("ORDER BY", 1)[1]
    assert "event_date" in order_clause
    assert "event_dates.id" in order_clause


async def test_list_for_client_filters_null_or_own_client_id() -> None:
    client_id = uuid4()
    session = _FakeSession()
    repo = SqlAlchemyEventRepository(session)  # type: ignore[arg-type]

    await repo.list_for_client(client_id=client_id, page=1, page_size=50)

    assert len(session.statements) == 2
    page_sql = _compiled(session.statements[0])
    count_sql = _compiled(session.statements[1])
    assert "client_id IS NULL" in page_sql
    assert client_id.hex in page_sql
    assert "client_id IS NULL" in count_sql


async def test_list_for_client_only_filters_by_client_id_only() -> None:
    client_id = uuid4()
    session = _FakeSession()
    repo = SqlAlchemyEventRepository(session)  # type: ignore[arg-type]

    await repo.list_for_client_only(client_id)

    page_sql = _compiled(session.statements[0])
    assert "client_id IS NULL" not in page_sql
    assert client_id.hex in page_sql


# ── delete_by_year ────────────────────────────────────────────────────────────


async def test_delete_by_year_general_filters_client_id_null() -> None:
    session = _FakeSession(rowcount=3)
    repo = SqlAlchemyEventRepository(session)  # type: ignore[arg-type]

    deleted = await repo.delete_by_year(year=2026, scope="general")

    assert deleted == 3
    sql = _compiled(session.statements[0])
    assert "DELETE FROM" in sql
    assert "client_id IS NULL" in sql
    assert str(date(2026, 1, 1)) in sql
    assert str(date(2027, 1, 1)) in sql


async def test_delete_by_year_clients_filters_client_id_not_null() -> None:
    session = _FakeSession(rowcount=5)
    repo = SqlAlchemyEventRepository(session)  # type: ignore[arg-type]

    deleted = await repo.delete_by_year(year=2026, scope="clients")

    assert deleted == 5
    sql = _compiled(session.statements[0])
    assert "client_id IS NOT NULL" in sql


async def test_delete_by_year_all_has_no_client_id_filter() -> None:
    session = _FakeSession(rowcount=8)
    repo = SqlAlchemyEventRepository(session)  # type: ignore[arg-type]

    deleted = await repo.delete_by_year(year=2026, scope="all")

    assert deleted == 8
    sql = _compiled(session.statements[0])
    assert "client_id" not in sql


async def test_delete_by_year_does_not_touch_other_years() -> None:
    session = _FakeSession()
    repo = SqlAlchemyEventRepository(session)  # type: ignore[arg-type]

    await repo.delete_by_year(year=2026, scope="all")

    sql = _compiled(session.statements[0])
    assert "2026-01-01" in sql
    assert "2027-01-01" in sql
    assert "2025" not in sql
