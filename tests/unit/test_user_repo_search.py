"""Unit tests for SqlAlchemyUserRepository.list_clients query construction.

No real database is available in this suite, so these tests capture the
statements passed to session.execute() and inspect their compiled SQL with
literal binds, instead of asserting on returned rows.
"""

from typing import Any

from app.database.user_module.user_repo import SqlAlchemyUserRepository


class _FakeResult:
    def all(self) -> list[Any]:
        return []

    def scalars(self) -> list[Any]:
        return []

    def scalar_one(self) -> int:
        return 0


class _FakeSession:
    def __init__(self) -> None:
        self.statements: list[Any] = []

    async def execute(self, stmt: Any) -> _FakeResult:
        self.statements.append(stmt)
        return _FakeResult()


def _compiled(stmt: Any) -> str:
    return str(stmt.compile(compile_kwargs={"literal_binds": True}))


async def test_search_filter_applied_to_page_and_count_query() -> None:
    session = _FakeSession()
    repo = SqlAlchemyUserRepository(session)  # type: ignore[arg-type]

    await repo.list_clients(page=1, page_size=50, search="maria")

    assert len(session.statements) == 2
    page_sql = _compiled(session.statements[0])
    count_sql = _compiled(session.statements[1])
    assert "LIKE" in page_sql
    assert "LIKE" in count_sql


async def test_search_term_is_stripped() -> None:
    session = _FakeSession()
    repo = SqlAlchemyUserRepository(session)  # type: ignore[arg-type]

    await repo.list_clients(page=1, page_size=50, search="  maria  ")

    page_sql = _compiled(session.statements[0])
    assert "%maria%" in page_sql


async def test_blank_search_is_treated_as_absent() -> None:
    session = _FakeSession()
    repo = SqlAlchemyUserRepository(session)  # type: ignore[arg-type]

    await repo.list_clients(page=1, page_size=50, search="   ")

    page_sql = _compiled(session.statements[0])
    assert "LIKE" not in page_sql


async def test_none_search_is_treated_as_absent() -> None:
    session = _FakeSession()
    repo = SqlAlchemyUserRepository(session)  # type: ignore[arg-type]

    await repo.list_clients(page=1, page_size=50)

    page_sql = _compiled(session.statements[0])
    assert "LIKE" not in page_sql


async def test_search_wildcards_are_escaped_as_literals() -> None:
    session = _FakeSession()
    repo = SqlAlchemyUserRepository(session)  # type: ignore[arg-type]

    await repo.list_clients(page=1, page_size=50, search="50%_off")

    page_sql = _compiled(session.statements[0])
    assert r"%50\%\_off%" in page_sql
    assert "ESCAPE '\\'" in page_sql


async def test_default_order_is_created_at_desc_with_id_tiebreak() -> None:
    session = _FakeSession()
    repo = SqlAlchemyUserRepository(session)  # type: ignore[arg-type]

    await repo.list_clients(page=1, page_size=50)

    page_sql = _compiled(session.statements[0])
    order_clause = page_sql.split("ORDER BY", 1)[1]
    assert "created_at DESC" in order_clause
    assert "users.id" in order_clause


async def test_sort_by_name_has_id_tiebreak() -> None:
    session = _FakeSession()
    repo = SqlAlchemyUserRepository(session)  # type: ignore[arg-type]

    await repo.list_clients(page=1, page_size=50, sort="name", order="asc")

    page_sql = _compiled(session.statements[0])
    order_clause = page_sql.split("ORDER BY", 1)[1]
    assert "users.name" in order_clause
    assert "users.id" in order_clause


async def test_sort_by_name_desc() -> None:
    session = _FakeSession()
    repo = SqlAlchemyUserRepository(session)  # type: ignore[arg-type]

    await repo.list_clients(page=1, page_size=50, sort="name", order="desc")

    page_sql = _compiled(session.statements[0])
    order_clause = page_sql.split("ORDER BY", 1)[1]
    assert "users.name DESC" in order_clause
