from pydantic import BaseModel
from typing import Optional


class TokenSchema(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenSchema(BaseModel):
    refresh_token: str


class TokenResponseSchema(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
