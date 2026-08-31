import os

# Set fake env vars before any app module is imported so Settings can load.
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
os.environ.setdefault("FRONTEND_URL", "http://localhost:3000")
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY", "test-anon-key")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-service-key")
os.environ.setdefault("SUPABASE_JWT_SECRET", "test-jwt-secret")

# O limite global de 60/min e por chave (IP "testclient" no TestClient), entao
# ficaria compartilhado por toda a suite e um teste derrubaria o seguinte.
# Fica desligado por padrao; test_rate_limit.py religa no proprio teste.
import pytest  # noqa: E402

from app.api.config.rate_limiter import limiter  # noqa: E402


@pytest.fixture(autouse=True)
def _disable_rate_limit() -> None:
    limiter.enabled = False
