from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class RequestLog(SQLModel, table=True):
    """One row per proxied request, recorded regardless of outcome.

    token_id/operation_id are nullable because unauthenticated or unmatched
    requests (401 before a token is resolved, 404 before an operation is
    resolved) still need to be recorded for denial-rate visibility.
    """

    __tablename__ = "request_logs"

    id: int | None = Field(default=None, primary_key=True)
    token_id: str | None = Field(default=None, foreign_key="tokens.id", index=True)
    operation_id: str | None = Field(default=None, foreign_key="operations.operation_id", index=True)
    method: str
    path: str
    status: int
    latency_ms: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), index=True)
