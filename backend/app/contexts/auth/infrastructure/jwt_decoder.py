import httpx
from jose import JWTError, jwk, jwt
from jose.exceptions import ExpiredSignatureError

from app.contexts.auth.domain.exceptions import TokenExpirado, TokenInvalido
from app.core.config import settings

_public_keys: dict[str, object] = {}


def _load_jwks() -> None:
    resp = httpx.get(f"{settings.SUPABASE_URL}/auth/v1/.well-known/jwks.json", timeout=10)
    resp.raise_for_status()
    for key_data in resp.json().get("keys", []):
        kid = key_data.get("kid", "")
        _public_keys[kid] = jwk.construct(key_data, algorithm=key_data.get("alg", "ES256"))


def decode_supabase_jwt(token: str) -> dict[str, object]:
    try:
        header = jwt.get_unverified_header(token)
        alg = header.get("alg", "HS256")

        if alg == "ES256":
            kid = str(header.get("kid", ""))
            if kid not in _public_keys:
                _load_jwks()
            key = _public_keys.get(kid)
            if key is None:
                raise TokenInvalido("Chave pública não encontrada para kid.")
            return jwt.decode(token, key, algorithms=["ES256"], audience="authenticated")

        return jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
        )
    except TokenInvalido:
        raise
    except ExpiredSignatureError as exc:
        raise TokenExpirado(str(exc)) from exc
    except JWTError as exc:
        raise TokenInvalido(str(exc)) from exc
