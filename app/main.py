from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import sentry_sdk
import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.config.logging import configure_logging
from app.api.config.middlewares.middlewares import (
    RequestLogMiddleware,
    SecurityHeadersMiddleware,
    StructlogContextMiddleware,
)
from app.api.config.rate_limiter import limiter
from app.api.config.settings import settings
from app.api.controllers.auth_module.auth_routes.auth_router import router as auth_router
from app.api.controllers.community_module.community_routes.admin_router import (
    admin_router as admin_community_router,
)
from app.api.controllers.community_module.community_routes.community_router import (
    router as community_router,
)
from app.api.controllers.content_module.content_routes.content_router import (
    admin_router as admin_content_router,
)
from app.api.controllers.content_module.content_routes.content_router import (
    comments_router,
)
from app.api.controllers.content_module.content_routes.content_router import (
    router as content_router,
)
from app.api.controllers.event_module.event_routes.admin_router import (
    admin_router as admin_events_router,
)
from app.api.controllers.event_module.event_routes.event_router import (
    router as events_router,
)
from app.api.controllers.metrics_module.metrics_routes.metrics_router import (
    admin_router as admin_metrics_router,
)
from app.api.controllers.metrics_module.metrics_routes.metrics_router import (
    router as metrics_router,
)
from app.api.controllers.product_module.product_routes.admin_router import (
    admin_router as admin_products_router,
)
from app.api.controllers.product_module.product_routes.product_router import (
    router as products_router,
)
from app.api.controllers.stage_module.stage_routes.admin_router import (
    admin_router as admin_stages_router,
)
from app.api.controllers.stage_module.stage_routes.stage_router import (
    router as stages_router,
)
from app.api.controllers.user_module.user_routes.admin_router import (
    admin_router as admin_clients_router,
)
from app.api.controllers.user_module.user_routes.user_router import router as users_router
from app.domain.shared.base_exceptions import AppException

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    configure_logging()
    if settings.SENTRY_DSN:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.ENVIRONMENT,
            traces_sample_rate=0.1,
        )
    logger.info("startup", environment=settings.ENVIRONMENT)
    yield
    logger.info("shutdown")


app = FastAPI(
    title="akeel Backend",
    version="0.1.0",
    docs_url="/docs" if settings.ENVIRONMENT != "prod" else "dev",
    redoc_url=None,
    lifespan=lifespan,
)

# ── Rate limiter ───────────────────────────────────────────────────────────────
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    # Sincrono de proposito: o SlowAPIMiddleware descarta handlers async
    # (slowapi.middleware.sync_check_limits) e cairia no envelope padrao dele.
    return JSONResponse(
        status_code=429,
        content={
            "error": {
                "code": "RATE_LIMIT_EXCEEDED",
                "message": "Limite de requisições excedido.",
            }
        },
    )


# ── Rate limit enforcement — sem este middleware os default_limits nao valem ───
app.add_middleware(SlowAPIMiddleware)

# ── Request body logger ────────────────────────────────────────────────────────
app.add_middleware(RequestLogMiddleware)

# ── Structlog context reset per request ───────────────────────────────────────
app.add_middleware(StructlogContextMiddleware)

# ── Security headers ───────────────────────────────────────────────────────────
app.add_middleware(SecurityHeadersMiddleware)

# ── CORS — must be outermost so headers are always present even on 500 ─────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Exception handlers ─────────────────────────────────────────────────────────
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    level = "warning" if exc.status < 500 else "error"
    log = logger.bind(path=request.url.path, code=exc.code)
    getattr(log, level)("app_exception")
    body: dict[str, Any] = {"error": {"code": exc.code, "message": exc.message}}
    if exc.details:
        body["error"]["details"] = exc.details
    return JSONResponse(status_code=exc.status, content=body)


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    logger.warning("validation_error", path=request.url.path)
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Dados inválidos.",
                "details": {".".join(map(str, e["loc"])): e["msg"] for e in exc.errors()},
            }
        },
    )


@app.exception_handler(Exception)
async def unhandled_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("unhandled_exception", path=request.url.path, exc_info=exc)
    sentry_sdk.capture_exception(exc)
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL_ERROR", "message": "Erro interno."}},
    )


# ── Health check ───────────────────────────────────────────────────────────────
@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


# ── Routers ────────────────────────────────────────────────────────────────────
app.include_router(auth_router, prefix="/api/v1")
app.include_router(community_router, prefix="/api/v1")
app.include_router(admin_community_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(admin_clients_router, prefix="/api/v1")
app.include_router(content_router, prefix="/api/v1")
app.include_router(admin_content_router, prefix="/api/v1")
app.include_router(comments_router, prefix="/api/v1")
app.include_router(metrics_router, prefix="/api/v1")
app.include_router(admin_metrics_router, prefix="/api/v1")
app.include_router(stages_router, prefix="/api/v1")
app.include_router(admin_stages_router, prefix="/api/v1")
app.include_router(products_router, prefix="/api/v1")
app.include_router(admin_products_router, prefix="/api/v1")
app.include_router(events_router, prefix="/api/v1")
app.include_router(admin_events_router, prefix="/api/v1")
