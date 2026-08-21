from datetime import datetime

from pydantic import BaseModel


class TokenCreate(BaseModel):
    name: str
    expires_at: datetime | None = None
    operation_ids: list[str] = []


class TokenUpdate(BaseModel):
    name: str | None = None
    expires_at: datetime | None = None
    operation_ids: list[str] | None = None


class TokenRead(BaseModel):
    id: str
    name: str
    created_at: datetime
    expires_at: datetime | None
    revoked_at: datetime | None
    last_used_at: datetime | None


class TokenDetailRead(TokenRead):
    operation_ids: list[str]


class TokenCreateResponse(TokenDetailRead):
    raw_token: str
