from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from jose import jwt

TEST_JWT_SECRET = "test-jwt-secret"


def fake_supabase_token(
    user_id: UUID,
    email: str = "test@test.com",
) -> str:
    now = datetime.now(tz=UTC)
    payload = {
        "sub": str(user_id),
        "email": email,
        "aud": "authenticated",
        "exp": int((now + timedelta(hours=1)).timestamp()),
        "iat": int(now.timestamp()),
        "role": "authenticated",
    }
    return jwt.encode(payload, TEST_JWT_SECRET, algorithm="HS256")


@pytest.fixture
def jwt_secret(monkeypatch: pytest.MonkeyPatch) -> str:
    monkeypatch.setenv("SUPABASE_JWT_SECRET", TEST_JWT_SECRET)
    return TEST_JWT_SECRET
