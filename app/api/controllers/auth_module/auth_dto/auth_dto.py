from dataclasses import dataclass
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

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

    email: EmailStr
    password: str = Field(min_length=1)


class TokensResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str
