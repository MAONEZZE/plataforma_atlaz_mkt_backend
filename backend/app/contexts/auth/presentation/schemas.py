from pydantic import BaseModel, ConfigDict


class LoginBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str
    password: str


class TokensResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str
