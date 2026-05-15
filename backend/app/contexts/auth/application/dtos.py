from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class UsuarioAutenticadoDTO:
    id: UUID
    email: str
    role: str


@dataclass(frozen=True)
class LoginInput:
    email: str
    password: str


@dataclass(frozen=True)
class TokensDTO:
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str
