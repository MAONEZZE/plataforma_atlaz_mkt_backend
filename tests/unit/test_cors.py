"""CORS: garante que so a origem configurada recebe Access-Control-Allow-Origin.

Regressao para dois bugs reais:
  1. FRONTEND_URL com barra final ("https://app.com/") nunca casa com o header
     Origin de um navegador, o que bloqueava 100% dos browsers silenciosamente.
  2. Confusao entre CORS e controle de acesso — CORS e enforcement do navegador,
     nao protege a API de curl/SSR/mobile. Ver test_cors_nao_e_controle_de_acesso.
"""

import pytest
from fastapi.testclient import TestClient

from app.api.config.settings import Settings, settings
from app.main import app

ALLOWED = settings.cors_origins[0]

_BASE_ENV = {
    "DATABASE_URL": "postgresql+asyncpg://t:t@localhost/t",
    "SUPABASE_URL": "https://t.supabase.co",
    "SUPABASE_ANON_KEY": "k",
    "SUPABASE_SERVICE_KEY": "k",
    "SUPABASE_JWT_SECRET": "s",
}


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _preflight(client: TestClient, origin: str):
    return client.options(
        "/api/v1/auth/login",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )


# ── Normalizacao da origem ────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("https://app.com/", ["https://app.com"]),
        ("https://app.com", ["https://app.com"]),
        ("https://app.com/,https://www.app.com/", ["https://app.com", "https://www.app.com"]),
        (" https://app.com/ , https://staging.app.com ", ["https://app.com", "https://staging.app.com"]),
    ],
)
def test_frontend_url_normaliza_barra_final_e_aceita_multiplas(
    raw: str, expected: list[str]
) -> None:
    s = Settings(FRONTEND_URL=raw, **_BASE_ENV)  # type: ignore[arg-type]
    assert s.cors_origins == expected


# ── Origem autorizada ─────────────────────────────────────────────────────────


def test_origem_autorizada_passa_no_preflight(client: TestClient) -> None:
    resp = _preflight(client, ALLOWED)
    assert resp.status_code == 200
    assert resp.headers["access-control-allow-origin"] == ALLOWED


def test_origem_autorizada_recebe_header_em_request_simples(client: TestClient) -> None:
    resp = client.get("/health", headers={"Origin": ALLOWED})
    assert resp.status_code == 200
    assert resp.headers["access-control-allow-origin"] == ALLOWED
    assert resp.headers["access-control-allow-credentials"] == "true"


def test_origem_autorizada_com_barra_final_e_recusada(client: TestClient) -> None:
    # Navegador nunca manda barra final; se alguem mandar, nao e a origem esperada.
    resp = _preflight(client, ALLOWED + "/")
    assert resp.status_code == 400


# ── Origem nao autorizada ─────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "origin",
    [
        "https://front.abc",
        "http://evil.com",
        "null",
        ALLOWED.replace("http", "https", 1) + ".evil.com",  # prefixo nao basta
    ],
)
def test_origem_nao_autorizada_e_recusada_no_preflight(
    client: TestClient, origin: str
) -> None:
    resp = _preflight(client, origin)
    assert resp.status_code == 400
    assert "access-control-allow-origin" not in resp.headers


def test_origem_nao_autorizada_nao_recebe_header_em_request_simples(
    client: TestClient,
) -> None:
    resp = client.get("/health", headers={"Origin": "https://front.abc"})
    # A requisicao roda no servidor; quem barra a LEITURA e o navegador,
    # e ele so barra porque o header abaixo esta ausente.
    assert resp.status_code == 200
    assert "access-control-allow-origin" not in resp.headers


def test_cors_nao_e_controle_de_acesso(client: TestClient) -> None:
    # Sem header Origin (curl, Postman, SSR, mobile) o CORS nem entra em cena.
    # Documenta que a protecao real e o JWT — ver test_route_auth_coverage.py.
    resp = client.get("/health")
    assert resp.status_code == 200
    assert "access-control-allow-origin" not in resp.headers
