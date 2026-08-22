from datetime import UTC, datetime, timedelta

from httpx import AsyncClient
from sqlmodel import Session

from app.models.request_log import RequestLog


def _add_log(session: Session, *, status: int, days_ago: int = 0) -> None:
    session.add(
        RequestLog(
            token_id=None,
            operation_id=None,
            method="GET",
            path="/x",
            status=status,
            latency_ms=1,
            created_at=datetime.now(UTC) - timedelta(days=days_ago),
        )
    )


async def test_usage_summary_requires_authentication(client: AsyncClient) -> None:
    response = await client.get("/_admin/api/usage/summary")
    assert response.status_code == 401


async def test_usage_summary_counts_denied_and_forwarded(
    logged_in_client: AsyncClient, session: Session
) -> None:
    _add_log(session, status=200)
    _add_log(session, status=200)
    _add_log(session, status=401)
    _add_log(session, status=403)
    _add_log(session, status=404)
    session.commit()

    response = await logged_in_client.get("/_admin/api/usage/summary")
    assert response.status_code == 200
    body = response.json()
    assert body["period_days"] == 7
    assert body["total_requests"] == 5
    assert body["denied_requests"] == 3
    assert body["forwarded_requests"] == 2


async def test_usage_summary_excludes_entries_outside_period(
    logged_in_client: AsyncClient, session: Session
) -> None:
    _add_log(session, status=200, days_ago=1)
    _add_log(session, status=200, days_ago=30)
    session.commit()

    response = await logged_in_client.get("/_admin/api/usage/summary?days=7")
    assert response.status_code == 200
    assert response.json()["total_requests"] == 1
