from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

from app.services.auth_module.jwt_decoder import decode_supabase_jwt


def _get_user_identifier(request: Request) -> str:
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        try:
            payload = decode_supabase_jwt(auth[7:])
            sub = payload.get("sub")
            if sub:
                return str(sub)
        except Exception:
            # Token invalido/expirado ainda vai ser recusado pelo get_current_user;
            # aqui so precisamos de uma chave de limite, entao caimos no IP.
            pass
    return get_remote_address(request)


limiter = Limiter(key_func=_get_user_identifier, default_limits=["60/minute"])
