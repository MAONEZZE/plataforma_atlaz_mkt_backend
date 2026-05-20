from jose import JWTError, jwt
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

from app.api.config.settings import settings


def _get_user_identifier(request: Request) -> str:
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth[7:]
        try:
            payload = jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                audience="authenticated",
            )
            sub = payload.get("sub")
            if sub:
                return str(sub)
        except JWTError:
            pass
    return get_remote_address(request)


limiter = Limiter(key_func=_get_user_identifier, default_limits=["60/minute"])
