import random
from datetime import UTC, datetime, timedelta

from sqlmodel import Session, delete

from app.config import settings
from app.models.request_log import RequestLog

# Probability of running a pruning DELETE on any given log insert. Keeps the
# table bounded without a dedicated scheduler/rotation job.
PRUNE_PROBABILITY = 0.02


def record_request_log(
    session: Session,
    *,
    token_id: str | None,
    operation_id: str | None,
    method: str,
    path: str,
    status_code: int,
    latency_ms: int,
) -> None:
    """Persists one proxied request's outcome.

    Occasionally prunes rows older than the configured retention window so the
    table doesn't grow unbounded, instead of running a separate scheduled job.
    """
    session.add(
        RequestLog(
            token_id=token_id,
            operation_id=operation_id,
            method=method,
            path=path,
            status=status_code,
            latency_ms=latency_ms,
        )
    )

    if random.random() < PRUNE_PROBABILITY:
        cutoff = datetime.now(UTC) - timedelta(days=settings.request_log_retention_days)
        session.exec(delete(RequestLog).where(RequestLog.created_at < cutoff))

    session.commit()
