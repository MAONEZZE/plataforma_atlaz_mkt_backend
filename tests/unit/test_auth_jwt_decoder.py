from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from jose import jwt

from app.domain.auth_module.auth_exceptions import ExpiredToken, InvalidToken

TEST_SECRET = "test-jwt-secret"


def _make_token(
    secret: str = TEST_SECRET,
    exp_delta: timedelta = timedelta(hours=1),
) -> str:
    now = datetime.now(tz=UTC)
    payload = {
        "sub": str(uuid4()),
        "email": "test@test.com",
        "aud": "authenticated",
        "exp": int((now + exp_delta).timestamp()),
        "iat": int(now.timestamp()),
        "role": "authenticated",
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def test_valid_token_returns_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.api.config import settings as cfg_module

    monkeypatch.setattr(cfg_module.settings, "SUPABASE_JWT_SECRET", TEST_SECRET)
    from app.services.auth_module import jwt_decoder

    token = _make_token()
    payload = jwt_decoder.decode_supabase_jwt(token)
    assert "sub" in payload


def test_expired_token_raises_token_expirado(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.api.config import settings as cfg_module

    monkeypatch.setattr(cfg_module.settings, "SUPABASE_JWT_SECRET", TEST_SECRET)
    from app.services.auth_module import jwt_decoder

    token = _make_token(exp_delta=timedelta(seconds=-1))
    with pytest.raises(ExpiredToken):
        jwt_decoder.decode_supabase_jwt(token)


def test_wrong_secret_raises_token_invalido(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.api.config import settings as cfg_module

    monkeypatch.setattr(cfg_module.settings, "SUPABASE_JWT_SECRET", TEST_SECRET)
    from app.services.auth_module import jwt_decoder

    token = _make_token(secret="wrong-secret")
    with pytest.raises(InvalidToken):
        jwt_decoder.decode_supabase_jwt(token)
