"""Rate limiting.

Regressao: o Limiter definia default_limits=["60/minute"], mas sem o
SlowAPIMiddleware registrado esses limites nunca eram aplicados — so o
@limiter.limit do login funcionava.
"""

import pytest
from fastapi.testclient import TestClient

from app.api.config.rate_limiter import limiter
from app.main import app


@pytest.fixture
def limited_client() -> TestClient:
    limiter.reset()
    limiter.enabled = True
    try:
        yield TestClient(app)
    finally:
        limiter.enabled = False
        limiter.reset()


def test_limite_global_e_aplicado(limited_client: TestClient) -> None:
    codigos = [limited_client.get("/health").status_code for _ in range(61)]
    assert codigos[:60] == [200] * 60
    assert codigos[60] == 429


def test_resposta_429_usa_o_envelope_padrao_da_api(limited_client: TestClient) -> None:
    # O SlowAPIMiddleware descarta exception handlers async e cairia no formato
    # {"error": "Rate limit exceeded: ..."} do slowapi, quebrando o contrato.
    for _ in range(61):
        resp = limited_client.get("/health")
    assert resp.status_code == 429
    assert resp.json() == {
        "error": {
            "code": "RATE_LIMIT_EXCEEDED",
            "message": "Limite de requisições excedido.",
        }
    }
