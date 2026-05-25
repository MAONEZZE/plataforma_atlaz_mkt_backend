# QA Review Report — Backend Atlaz MKT

> Generated: 2026-05-25  
> Source: Survey of 165 `.py` files across `app/api/`, `app/services/`, `app/domain/`, `app/database/`  
> Scope: 31 findings documented; 7 HIGH fixes applied in this cycle

---

## 1. Executive Summary

| Severity | Total | Fixed this cycle | Remaining |
|----------|-------|-----------------|-----------|
| HIGH | 7 | 7 | 0 |
| MED | 12 | 0 | 12 |
| LOW | 12 | 0 | 12 |
| **Total** | **31** | **7** | **24** |

**Hotspots:**
- `app/database/content_module/content_repo.py` — 2 HIGHs (model attrs, flush)
- `app/api/controllers/auth_module/` — 2 HIGHs (Bearer validation, DTO)
- `app/api/controllers/content_module/content_routes/content_router.py` — 1 HIGH (try-except)
- `app/database/community_module/community_repo.py` — 1 HIGH (SQL column name)
- `app/services/auth_module/logout_service.py` — 1 HIGH (async blocking)

**Bonus fixes applied (not in original HIGH list):**
- Wrong `*.auth_service.*`, `*.content_service.*`, `*.community_service.*`, `*.metrics_service.*`, `*.user_service.*` import paths — blocked entire test suite (19 files)
- `pydantic[email]` missing — added to support `EmailStr`

---

## 2. Master Table — All 31 Findings

| # | File | Sev | Problem | Status |
|---|------|-----|---------|--------|
| 1 | `app/database/content_module/content_repo.py:22-106` | HIGH | `TrackModel`, `ModuleModel`, `LessonModel`, `CommentModel` declared PT attrs (`titulo`, `descricao`, `ordem`, `duracao_minutos`, `texto`) but mappers read EN (`title`, `description`, `order`, `duration_minutes`, `text`) → `AttributeError` at runtime | **FIXED** |
| 2 | `app/database/community_module/community_repo.py:16,26` | HIGH | Raw SQL references column `inativo`; migration 0003 renamed to `inactive` | **FIXED** |
| 3 | `app/services/auth_module/logout_service.py:9` | HIGH | `client.auth.sign_out()` sync call inside `async def execute` — blocks event loop | **FIXED** |
| 4 | `app/database/content_module/content_repo.py:400-406` | HIGH | `unmark()` lacks `await self._session.flush()` after `execute()` — inconsistent with `mark_completed()` | **FIXED** |
| 5 | `app/api/controllers/content_module/content_routes/content_router.py:336-349,396-409` | HIGH | `create_track` and `create_module` had no try-except — domain exceptions leaked as raw 500 | **FIXED** |
| 6 | `app/api/controllers/auth_module/auth_routes/auth_router.py:109` | HIGH | Blind slice `[len("Bearer "):]` on Authorization header — malformed header passed wrong token to service | **FIXED** |
| 7 | `app/api/controllers/auth_module/auth_dto/auth_dto.py:32-36` | HIGH | `LoginBody` accepted empty email string and empty password — no `EmailStr` or `min_length` | **FIXED** |
| 8 | `app/api/main.py:87` | MED | `allow_origins=[settings.FRONTEND_URL]` without validation — empty/invalid setting causes unpredictable CORS | open |
| 9 | `app/api/controllers/content_module/content_routes/content_router.py:537-543` | MED | `page_size`/`page` lack consistent explicit defaults | open |
| 10 | `app/api/controllers/content_module/content_routes/content_router.py:583` | MED | `create_comment` returns `AuthorOut(name="")` hardcoded | open |
| 11 | `app/api/config/rate_limiter.py:14-24` | MED | `JWTError` silenced in fallback to IP — masks misconfiguration | open |
| 12 | `app/api/controllers/content_module/content_routes/content_router.py` (reorder) | MED | `ReorderIn` has no uniqueness/sequence validation | open |
| 13 | `app/services/metrics_module/get_admin_consolidated.py:29-49` | MED | Loads all metrics into memory, paginates in Python — OOM risk at scale | open |
| 14 | `app/services/content_module/lessons/mark_completed.py:14-19` | MED | No validation that lesson exists or user has access; race condition possible | open |
| 15 | `app/services/user_module/supabase_storage_gateway.py:21-26` | MED | Upload/`get_public_url` without try-catch — partial failure leaves `photo_url` broken | open |
| 16 | `app/database/shared/storage_client.py:11-13` | MED | No error handling on Supabase upload | open |
| 17 | `app/database/shared/db_factory.py:19-21` | MED | `async with begin()` auto-commit behavior undocumented — rollback semantics unclear | open |
| 18 | `app/database/migrations/versions/0003_rename_pt_to_en.py:119-195` | MED | `downgrade()` does not revert trigger bodies — migration effectively irreversible | open |
| 19 | `app/services/content_module/tracks/list_with_progress.py:25-52` | MED→HIGH | N+1 grave: tracks→modules→lessons in loop — promote to HIGH if latency metrics confirm | open |
| 20 | `app/api/config/exception_handlers/handlers.py` | LOW | File unused — `main.py` registers handlers inline | open |
| 21 | `app/main.py:138-140` | LOW | `/health` has no auth (likely intentional — document it) | open |
| 22 | `app/api/controllers/auth_module/auth_routes/auth_router.py:103-114` | LOW | Logout 204 includes unnecessary response body | open |
| 23 | `app/services/user_module/image_validation.py:1-12` | LOW | Validates magic bytes, not structure — truncated JPEG passes; use `PIL.Image.open()` | open |
| 24 | `app/services/metrics_module/create_metric.py:51`, `update_metric.py:40` | LOW | 28-day edit window hardcoded — move to `settings.METRIC_EDIT_WINDOW_DAYS` | open |
| 25 | `app/services/content_module/tracks/get_with_modules.py:42-64` | LOW | Minor N+1: loop calling `list_by_module()` | open |
| 26 | `app/services/auth_module/jwt_decoder.py:33-37` | LOW | `exp`/`iat` validation relies on `jose` implicitly — add explicit assertion | open |
| 27 | `app/domain/shared/base_value_objects.py:12-13` | LOW | Email regex too permissive — `a@b` passes | open |
| 28 | `app/database/migrations/versions/0001_initial_schema.py:161` | LOW | `EXTRACT(DOW)=1` check redundant with domain — document intent | open |
| 29 | `app/database/migrations/versions/0001_initial_schema.py:146` | LOW | No index on `comentario(usuario_id)` — full scan on user queries | open |
| 30 | `app/api/controllers/metrics_module/metrics_routes/metrics_router.py:249` | LOW | `busca` query param unsanitized | open |
| 31 | `app/api/controllers/auth_module/auth_dto/auth_dto.py` | LOW | Other DTOs also lack `min_length` review | open |

---

## 3. Baseline vs After

### Before (baseline captured 2026-05-25)

| Tool | Result |
|------|--------|
| `ruff` | 4 errors (import sort) |
| `mypy` | 3 errors in 2 files (`import-not-found` ×2, duplicate module ×1) |
| `lint-imports` | BROKEN — `domain` imports `presentation` |
| `pytest` | 18 collection errors (wrong import paths); 0 tests ran |

### After (post-fix)

| Tool | Result |
|------|--------|
| `ruff` | **0 errors** ✓ |
| `mypy` | **1 error** (duplicate module only — pre-existing config issue) |
| `lint-imports` | BROKEN — same pre-existing violation in `auth_repo_interface` |
| `pytest` | **234 passed, 0 failed** ✓ |
| `/health` | **200 OK** ✓ |

### Net improvement
- ruff: 4 → 0 errors  
- mypy: 3 → 1 error  
- pytest: 0 → 234 tests passing (entire suite unblocked by fixing 19 wrong import paths)  
- Coverage: 84% total

---

## 4. Fixes Applied — Detail

### Fix #1 — SQLAlchemy models aligned with migration 0003
**File:** `app/database/content_module/content_repo.py`  
**Change:** Python attribute names in `TrackModel`, `ModuleModel`, `LessonModel`, `CommentModel` renamed from PT to EN. `mapped_column("pt_col_name", ...)` used to preserve DB column names (which migration 0003 did NOT rename for these tables).

```python
# Before
titulo: Mapped[str] = mapped_column(Text, nullable=False)

# After
title: Mapped[str] = mapped_column("titulo", Text, nullable=False)
```

### Fix #2 — community_repo SQL column name
**File:** `app/database/community_module/community_repo.py:16,26`  
**Change:** `inativo` → `inactive` in both raw SQL queries.

### Fix #3 — logout_service async
**File:** `app/services/auth_module/logout_service.py:9`  
**Change:** `self._gateway.sign_out(access_token)` → `await asyncio.to_thread(self._gateway.sign_out, access_token)`

### Fix #4 — unmark() flush
**File:** `app/database/content_module/content_repo.py:400-406`  
**Change:** Added `await self._session.flush()` after `execute()` in `unmark()`.

### Fix #5 — create_track / create_module try-except
**File:** `app/api/controllers/content_module/content_routes/content_router.py`  
**Change:** Wrapped `use_case.execute()` in try-except matching `update_track`/`update_module` pattern. Domain exceptions now map to structured `AppException` instead of leaking as 500.

### Fix #6 — Authorization header Bearer validation
**File:** `app/api/controllers/auth_module/auth_routes/auth_router.py:109`  
**Change:**
```python
# Before
token = request.headers.get("Authorization", "")[len("Bearer "):]

# After
auth = request.headers.get("Authorization", "")
if not auth.startswith("Bearer "):
    raise AppException("INVALID_AUTH_HEADER", "Authorization header inválido.", 401)
token = auth[7:]
```

### Fix #7 — LoginBody validation
**File:** `app/api/controllers/auth_module/auth_dto/auth_dto.py`  
**Change:** `email: str` → `email: EmailStr`, `password: str` → `password: str = Field(min_length=1)`.

### Bonus — Wrong import paths (19 files)
All `*.auth_service.*`, `*.content_service.*`, `*.community_service.*`, `*.metrics_service.*`, `*.user_service.*` subdirectory segments removed from import paths. The extra subdirectory level didn't exist after the flat-layer refactor, blocking the entire test suite from collecting.

---

## 5. Recommendations for Next Cycle (MED + LOW)

**Priority 1 — MED items to fix next:**
1. **Finding #19** — N+1 tracks→modules→lessons (`list_with_progress.py`): promote to HIGH, fix with eager loading or batched query.
2. **Finding #14** — `mark_completed` lacks lesson existence check + race condition.
3. **Finding #13** — `get_admin_consolidated` full in-memory pagination — add DB-level pagination.
4. **Finding #15/16** — Supabase upload/storage without error handling.

**Priority 2 — MED infra items:**
5. **Finding #18** — Migration 0003 `downgrade()` doesn't revert triggers — document as irreversible or add idempotent revert.
6. **Finding #17** — Document `db_factory.py` rollback semantics in a docstring.
7. **Finding #8** — CORS `FRONTEND_URL` validation at startup.

**Priority 3 — LOW tech debt:**
8. **Finding #23** — Replace magic-byte image check with `PIL.Image.open()`.
9. **Finding #29** — Add index on `comentario(usuario_id)`.
10. **Finding #24** — Extract 28-day constant to settings.
11. **Finding #27** — Tighten email regex in `base_value_objects.py`.

**Architecture note:** Migration 0003 renamed tables but left most column names in Portuguese inside `tracks`, `modules`, `lessons`, `comments`. Fix #1 uses SQLAlchemy column aliasing as a bridge. A future migration renaming those columns to English would allow removing the `mapped_column("pt_name", ...)` wrappers and fully simplify the ORM models.
