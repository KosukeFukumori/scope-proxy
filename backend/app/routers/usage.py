from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Query
from sqlalchemy import func
from sqlmodel import select

from app.deps import CurrentUserDep, SessionDep
from app.models.request_log import RequestLog
from app.schemas.request_log import UsageSummary

router = APIRouter(prefix="/api/usage", tags=["usage"])

# Statuses that represent the proxy rejecting a request itself (auth/permission/routing
# failures), as opposed to a request that was forwarded to the upstream backend.
DENIED_STATUSES = (401, 403, 404)


@router.get("/summary", response_model=UsageSummary)
def get_usage_summary(
    session: SessionDep,
    current_user: CurrentUserDep,
    days: int = Query(default=7, ge=1, le=90),
) -> UsageSummary:
    cutoff = datetime.now(UTC) - timedelta(days=days)

    total_requests = session.exec(
        select(func.count()).select_from(RequestLog).where(RequestLog.created_at >= cutoff)
    ).one()
    denied_requests = session.exec(
        select(func.count())
        .select_from(RequestLog)
        .where(RequestLog.created_at >= cutoff, RequestLog.status.in_(DENIED_STATUSES))
    ).one()

    return UsageSummary(
        period_days=days,
        total_requests=total_requests,
        denied_requests=denied_requests,
        forwarded_requests=total_requests - denied_requests,
    )
