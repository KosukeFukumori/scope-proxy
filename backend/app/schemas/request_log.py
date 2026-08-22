from datetime import datetime

from pydantic import BaseModel


class RequestLogRead(BaseModel):
    id: int
    token_id: str | None
    operation_id: str | None
    method: str
    path: str
    status: int
    latency_ms: int
    created_at: datetime


class UsageSummary(BaseModel):
    period_days: int
    total_requests: int
    denied_requests: int
    forwarded_requests: int
