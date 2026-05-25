# Merged from: contexts/auth/application/dtos.py + contexts/auth/presentation/schemas.py
from dataclasses import dataclass
from uuid import UUID

from pydantic import BaseModel, ConfigDict

# ── Application DTOs ───────────────────────────────────────────────────────────

@dataclass(frozen=True)
class AuthenticatedUserDTO:
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


# ── Presentation Schemas ───────────────────────────────────────────────────────

class LoginBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str
    password: str


class TokensResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str
