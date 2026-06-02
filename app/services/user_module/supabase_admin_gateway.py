from typing import Protocol
from uuid import UUID

from supabase import Client
from supabase_auth.errors import AuthApiError

from app.domain.user_module.user_exceptions import (
    EmailAlreadyRegistered,
    SupabaseAdminError,
)


class SupabaseAdminUserGateway(Protocol):
    def create_user(self, email: str, password: str, name: str, role: str) -> UUID: ...
    def delete_user(self, user_id: UUID) -> None: ...


class SupabaseAdminUserGatewayImpl:
    def __init__(self, client: Client) -> None:
        self._client = client

    def create_user(self, email: str, password: str, name: str, role: str) -> UUID:
        try:
            response = self._client.auth.admin.create_user(
                {
                    "email": email,
                    "password": password,
                    "email_confirm": True,
                    "user_metadata": {"name": name, "role": role},
                }
            )
        except AuthApiError as exc:
            if _is_email_exists(exc):
                raise EmailAlreadyRegistered("Email já cadastrado.") from exc
            raise SupabaseAdminError(str(exc)) from exc

        user = response.user
        if user is None:
            raise SupabaseAdminError("Resposta inesperada da API do Supabase.")
        return UUID(str(user.id))

    def delete_user(self, user_id: UUID) -> None:
        try:
            self._client.auth.admin.delete_user(str(user_id))
        except AuthApiError as exc:
            raise SupabaseAdminError(str(exc)) from exc


def _is_email_exists(exc: AuthApiError) -> bool:
    code = getattr(exc, "code", None)
    if code == "email_exists":
        return True
    msg = str(exc).lower()
    return "already" in msg or "registered" in msg
