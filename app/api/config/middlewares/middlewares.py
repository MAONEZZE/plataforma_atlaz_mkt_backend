import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

_LOG_DIR = Path(__file__).resolve().parents[4] / "logs"
_LOG_FILE = _LOG_DIR / "requests.log"


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Any) -> Response:
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response


class StructlogContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Any) -> Response:
        structlog.contextvars.clear_contextvars()
        response: Response = await call_next(request)
        return response


class RequestLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Any) -> Response:
        body_obj: Any = None
        content_type = request.headers.get("content-type", "")
        if "multipart/form-data" not in content_type and "application/octet-stream" not in content_type:
            try:
                body_bytes = await request.body()
                if body_bytes:
                    try:
                        body_obj = json.loads(body_bytes)
                    except Exception:
                        body_obj = body_bytes.decode(errors="replace")
            except Exception:
                pass

        timestamp = datetime.now(timezone.utc).isoformat()
        endpoint = f"{request.method} {request.url.path}"
        line = f"{timestamp} {endpoint}: {json.dumps(body_obj, ensure_ascii=False)}\n"

        try:
            _LOG_DIR.mkdir(parents=True, exist_ok=True)
            with _LOG_FILE.open("a", encoding="utf-8") as f:
                f.write(line)
        except Exception:
            pass

        return await call_next(request)
