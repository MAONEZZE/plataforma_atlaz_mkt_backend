# Plan — Metric Rename + Stage & Product Entities

## Context

Three changes requested:

1. **Rename metric fields** across entire backend:
   - `calls_scheduled` → `meetings_held` (was "Ligação Agendada", becomes "Reunião Realizada")
   - `meetings_scheduled` → `sales` (was "Reuniões Agendadas", becomes "Vendas")
2. **New entity `Stage`** (Etapa): id/text, with per-client `done` flag on the join row. N:M to client users. Admin-only C/U/D; clients read their own.
3. **New entity `Product`** (Produto): id/name/value. 1:N — each client has at most one product; one product can serve many clients. Admin-only C/U/D; clients read. Assignable at client creation and via dedicated admin endpoint.

Repo: layered arch (`app/api`, `app/domain`, `app/database`, `app/services`, `tests`). Patterns to mirror: `app/api/controllers/user_module/user_routes/admin_router.py` (admin CRUD) and `app/database/content_module/content_repo.py` `StudentLessonModel` (N:M join with extra column).

Auth guard exists: `require_admin` in `app/api/config/dependencies/auth_deps.py:43`. Current user dep returns `User` (id, role). Roles: `cliente`, `admin`.

---

## Part 1 — Metric rename (DB + code)

### 1.1 New alembic migration `0004_rename_metric_columns.py`

Path: `app/database/migrations/versions/0004_rename_metric_columns.py`. Down rev `0003`.

```python
op.alter_column("weekly_metrics", "calls_scheduled", new_column_name="meetings_held", schema="ATZ_HUB")
op.alter_column("weekly_metrics", "meetings_scheduled", new_column_name="sales", schema="ATZ_HUB")
```

Downgrade reverses.

### 1.2 Code rename (mechanical, two find/replace pairs)

Across the following files, replace `calls_scheduled` → `meetings_held` and `meetings_scheduled` → `sales` (including `*_total` derived names like `calls_scheduled_total` → `meetings_held_total`):

- `app/domain/metrics_module/metrics_model.py` — `WeeklyMetric`, `UserMonthlyMetrics` dataclasses
- `app/database/metrics_module/metrics_repo.py` — `WeeklyMetricModel` columns, create/update/mapper, `sum_by_month`, `list_clients_with_metrics_month`
- `app/api/controllers/metrics_module/metrics_dto/metrics_dto.py` — 12 DTO classes
- `app/api/controllers/metrics_module/metrics_routes/metrics_router.py` — response builders, delta calcs, series, aggregates
- `app/services/metrics_module/create_metric.py`
- `app/services/metrics_module/update_metric.py`
- `app/services/metrics_module/get_dashboard_summary.py`
- `app/services/metrics_module/get_dashboard_series.py`
- `app/services/metrics_module/get_admin_consolidated.py`
- `tests/unit/metrics/test_routers.py`
- `tests/unit/metrics/test_use_cases.py`

Do NOT touch `0001` or `0003` migrations — history is immutable.

---

## Part 2 — Stage entity (Etapa)

Schema: `stages` table holds catalog (`id`, `text`). Join table `user_stages` carries `done`.

### 2.1 Migration `0005_create_stages.py`

```python
op.create_table(
    "stages",
    sa.Column("id", PGUUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
    sa.Column("text", sa.Text, nullable=False),
    sa.Column("created_at", sa.TIMESTAMP, server_default=sa.text("now()")),
    schema="ATZ_HUB",
)
op.create_table(
    "user_stages",
    sa.Column("user_id", PGUUID, sa.ForeignKey("ATZ_HUB.users.id", ondelete="CASCADE"), primary_key=True),
    sa.Column("stage_id", PGUUID, sa.ForeignKey("ATZ_HUB.stages.id", ondelete="CASCADE"), primary_key=True),
    sa.Column("done", sa.Boolean, nullable=False, server_default=sa.text("false")),
    sa.Column("updated_at", sa.TIMESTAMP, server_default=sa.text("now()")),
    schema="ATZ_HUB",
)
```

### 2.2 Module files (mirror `user_module` patterns)

- `app/domain/stage_module/stage_model.py` — `@dataclass Stage(id, text)`, `@dataclass UserStage(user_id, stage_id, done)`
- `app/domain/stage_module/stage_repo_interface.py` — `StageRepository(Protocol)` with `create`, `update`, `delete`, `get_by_id`, `list_all`, `list_for_user`, `attach_to_user`, `detach_from_user`, `set_done`
- `app/domain/stage_module/stage_exceptions.py` — `StageNotFound`, `StageAlreadyAttached`
- `app/database/stage_module/stage_repo.py` — `StageModel(Base)`, `UserStageModel(Base)` (composite PK, follow `StudentLessonModel`), `SqlAlchemyStageRepository`
- `app/services/stage_module/` — `create_stage.py`, `update_stage.py`, `delete_stage.py`, `list_stages.py`, `list_user_stages.py`, `attach_stage.py`, `detach_stage.py`, `set_stage_done.py`
- `app/api/controllers/stage_module/stage_dto/stage_dto.py` — request/response models
- `app/api/controllers/stage_module/stage_routes/stage_router.py` — client read endpoint (`GET /stages/me`, `PATCH /stages/me/{stage_id}` for `done` toggle)
- `app/api/controllers/stage_module/stage_routes/admin_router.py` — admin CRUD: `POST /admin/stages`, `GET /admin/stages`, `PATCH /admin/stages/{id}`, `DELETE /admin/stages/{id}`, `POST /admin/clients/{user_id}/stages/{stage_id}` (attach), `DELETE /admin/clients/{user_id}/stages/{stage_id}`

Wire both routers in `app/main.py` (or the router registry it uses).

### 2.3 Permissions

- Admin routes: `Depends(require_admin)` on every handler.
- Client toggle of `done`: client-facing router uses `get_current_user` and asserts the `user_stages` row belongs to caller.

### 2.4 Tests

`tests/unit/stages/test_use_cases.py`, `tests/unit/stages/test_routers.py`, `tests/integration/test_stages_integration.py` — mirror existing admin client integration test.

---

## Part 3 — Product entity (Produto)

### 3.1 Migration `0006_create_products.py`

```python
op.create_table(
    "products",
    sa.Column("id", PGUUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
    sa.Column("name", sa.Text, nullable=False),
    sa.Column("value", sa.Numeric(12, 2), nullable=False),
    sa.Column("created_at", sa.TIMESTAMP, server_default=sa.text("now()")),
    schema="ATZ_HUB",
)
op.add_column(
    "users",
    sa.Column("product_id", PGUUID, sa.ForeignKey("ATZ_HUB.products.id", ondelete="SET NULL"), nullable=True),
    schema="ATZ_HUB",
)
```

Use `Numeric(12, 2)` for currency value (avoid float).

### 3.2 Module files

- `app/domain/product_module/product_model.py` — `@dataclass Product(id, name, value: Decimal)`
- `app/domain/product_module/product_repo_interface.py` — `ProductRepository` with `create`, `update`, `delete`, `get_by_id`, `list_all`
- `app/domain/product_module/product_exceptions.py` — `ProductNotFound`, `ProductInUse` (block delete if any user still references it)
- `app/database/product_module/product_repo.py` — `ProductModel(Base)`, `SqlAlchemyProductRepository`
- Extend `app/database/user_module/user_repo.py` `UserModel` with `product_id` column + add `assign_product(user_id, product_id)` method on `SqlAlchemyUserRepository`. Update `_to_entity` to surface `product_id` on the `User` dataclass (add field in `app/domain/user_module/user_model.py`).
- `app/services/product_module/` — `create_product.py`, `update_product.py`, `delete_product.py`, `list_products.py`, `assign_product_to_client.py`
- `app/api/controllers/product_module/product_dto/product_dto.py`
- `app/api/controllers/product_module/product_routes/product_router.py` — `GET /products` (client read), `GET /products/{id}`
- `app/api/controllers/product_module/product_routes/admin_router.py` — `POST/GET/PATCH/DELETE /admin/products`, `PATCH /admin/clients/{user_id}/product` (assign)

### 3.3 Extend `CreateClient` service

Modify `app/services/user_module/create_client_service.py`: add optional `product_id: UUID | None` to input; if set, validate product exists (call `ProductRepository.get_by_id`); on save, persist `product_id` on `users` row.

Update `CreateClientBody` DTO in `app/api/controllers/user_module/user_dto/user_dto.py` to accept optional `product_id`.

### 3.4 Tests

`tests/unit/products/`, `tests/integration/test_products_integration.py`. Cover: admin C/U/D, client read, deleting a product referenced by a user, assigning at create + later.

---

## Critical files modified (summary)

- New migrations: `0004_rename_metric_columns.py`, `0005_create_stages.py`, `0006_create_products.py`
- New modules: `app/{domain,database,services,api/controllers}/stage_module/**`, `app/{domain,database,services,api/controllers}/product_module/**`
- Edited metrics module (rename): `app/domain/metrics_module/metrics_model.py`, `app/database/metrics_module/metrics_repo.py`, `app/api/controllers/metrics_module/**`, `app/services/metrics_module/*.py`, `tests/unit/metrics/**`
- Edited user module: `app/domain/user_module/user_model.py` (add `product_id`), `app/database/user_module/user_repo.py` (column + assign), `app/services/user_module/create_client_service.py` (accept product_id), `app/api/controllers/user_module/user_dto/user_dto.py`
- `app/main.py` — register new routers

---

## Verification

1. `alembic upgrade head` runs clean (or whatever the project's migration command is — check `docker-entrypoint` or README).
2. `alembic downgrade -3` then `upgrade head` round-trips clean.
3. `pytest tests/unit/metrics tests/unit/stages tests/unit/products tests/integration` green.
4. Boot app (`python -m app.main` or docker entrypoint). Hit:
   - `POST /admin/stages` (admin token) → 201
   - `POST /admin/products` → 201
   - `POST /admin/clients` with `product_id` → 201, response shows `product_id`
   - `POST /admin/clients/{uid}/stages/{sid}` → 201
   - `GET /stages/me` (client token) → list with `done=false`
   - `PATCH /stages/me/{sid}` `{done: true}` → 200
   - `GET /admin/dashboard/...` returns new field names `meetings_held`, `sales`
5. Grep verifies no `calls_scheduled` / `meetings_scheduled` strings remain (except in migration `0003` history).
