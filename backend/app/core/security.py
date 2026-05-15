from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError

from app.core.config import settings
from app.core.exceptions import AppException


def decode_supabase_jwt(token: str) -> dict[str, object]:
    try:
        return jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
        )
    except ExpiredSignatureError as exc:
        raise AppException("TOKEN_EXPIRED", "Token expirado.", 401) from exc
    except JWTError as exc:
        raise AppException("TOKEN_INVALID", "Token inválido.", 401) from exc
