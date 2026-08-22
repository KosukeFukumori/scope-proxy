import hashlib
from datetime import UTC, datetime, timedelta

from httpx import AsyncClient
from sqlmodel import Session, select

from app.models.operation import Operation
from app.models.request_log import RequestLog
from app.models.token import Token, TokenPermission


def _assert_utc_aware(value: str) -> None:
    """Assert a serialized datetime string carries a UTC offset (`+00:00` / `Z`)."""
    parsed = datetime.fromisoformat(value)
    assert parsed.tzinfo is not None
    assert parsed.utcoffset() == timedelta(0)


async def test_list_tokens_requires_authentication(client: AsyncClient) -> None:
    response = await client.get("/_admin/api/tokens")
    assert response.status_code == 401


async def test_create_token_returns_raw_value_once(logged_in_client: AsyncClient, session: Session) -> None:
    operation = Operation(operation_id="getUser", method="GET", path="/users/{id}", is_active=True)
    session.add(operation)
    session.commit()

    response = await logged_in_client.post(
        "/_admin/api/tokens",
        json={"name": "ci-token", "operation_ids": ["getUser"]},
    )
    assert response.status_code == 201
    body = response.json()
    assert "raw_token" in body
    assert body["operation_ids"] == ["getUser"]

    stored = session.exec(select(Token).where(Token.name == "ci-token")).first()
    assert stored is not None
    assert stored.token_hash == hashlib.sha256(body["raw_token"].encode()).hexdigest()
    assert stored.token_hash != body["raw_token"]


async def test_list_and_get_token(logged_in_client: AsyncClient) -> None:
    create_response = await logged_in_client.post("/_admin/api/tokens", json={"name": "t1"})
    token_id = create_response.json()["id"]

    list_response = await logged_in_client.get("/_admin/api/tokens")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1
    assert "raw_token" not in list_response.json()[0]

    detail_response = await logged_in_client.get(f"/_admin/api/tokens/{token_id}")
    assert detail_response.status_code == 200
    assert detail_response.json()["name"] == "t1"
    assert "raw_token" not in detail_response.json()


async def test_update_token_permissions(logged_in_client: AsyncClient, session: Session) -> None:
    session.add(Operation(operation_id="opA", method="GET", path="/a", is_active=True))
    session.add(Operation(operation_id="opB", method="GET", path="/b", is_active=True))
    session.commit()

    create_response = await logged_in_client.post(
        "/_admin/api/tokens", json={"name": "t1", "operation_ids": ["opA"]}
    )
    token_id = create_response.json()["id"]

    update_response = await logged_in_client.patch(
        f"/_admin/api/tokens/{token_id}",
        json={"name": "renamed", "operation_ids": ["opB"]},
    )
    assert update_response.status_code == 200
    body = update_response.json()
    assert body["name"] == "renamed"
    assert body["operation_ids"] == ["opB"]

    remaining = session.exec(select(TokenPermission).where(TokenPermission.token_id == token_id)).all()
    assert len(remaining) == 1
    assert remaining[0].operation_id == "opB"


async def test_update_token_expires_at_unset_keeps_existing_value(logged_in_client: AsyncClient) -> None:
    create_response = await logged_in_client.post(
        "/_admin/api/tokens",
        json={"name": "t1", "expires_at": "2030-01-01T00:00:00Z"},
    )
    token_id = create_response.json()["id"]
    assert create_response.json()["expires_at"] is not None

    # Field omitted entirely -> no change to expires_at.
    update_response = await logged_in_client.patch(
        f"/_admin/api/tokens/{token_id}",
        json={"name": "renamed"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["expires_at"] is not None


async def test_update_token_expires_at_null_clears_value(logged_in_client: AsyncClient) -> None:
    create_response = await logged_in_client.post(
        "/_admin/api/tokens",
        json={"name": "t1", "expires_at": "2030-01-01T00:00:00Z"},
    )
    token_id = create_response.json()["id"]
    assert create_response.json()["expires_at"] is not None

    # Field explicitly set to null -> expires_at is cleared (token becomes non-expiring).
    update_response = await logged_in_client.patch(
        f"/_admin/api/tokens/{token_id}",
        json={"name": "t1", "expires_at": None},
    )
    assert update_response.status_code == 200
    assert update_response.json()["expires_at"] is None


async def test_revoke_token(logged_in_client: AsyncClient) -> None:
    create_response = await logged_in_client.post("/_admin/api/tokens", json={"name": "t1"})
    token_id = create_response.json()["id"]

    revoke_response = await logged_in_client.post(f"/_admin/api/tokens/{token_id}/revoke")
    assert revoke_response.status_code == 200
    assert revoke_response.json()["revoked_at"] is not None


async def test_token_not_found_for_other_user(logged_in_client: AsyncClient) -> None:
    response = await logged_in_client.get("/_admin/api/tokens/9999")
    assert response.status_code == 404


async def test_list_token_logs_returns_recent_entries_newest_first(
    logged_in_client: AsyncClient, session: Session
) -> None:
    create_response = await logged_in_client.post("/_admin/api/tokens", json={"name": "t1"})
    token_id = create_response.json()["id"]

    session.add(
        RequestLog(
            token_id=token_id,
            operation_id="getUser",
            method="GET",
            path="/users/1",
            status=200,
            latency_ms=12,
            created_at=datetime(2024, 1, 1, tzinfo=UTC),
        )
    )
    session.add(
        RequestLog(
            token_id=token_id,
            operation_id="getUser",
            method="GET",
            path="/users/1",
            status=403,
            latency_ms=3,
            created_at=datetime(2024, 1, 2, tzinfo=UTC),
        )
    )
    session.commit()

    response = await logged_in_client.get(f"/_admin/api/tokens/{token_id}/logs")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert body[0]["status"] == 403
    assert body[1]["status"] == 200


async def test_list_token_logs_requires_ownership(logged_in_client: AsyncClient) -> None:
    response = await logged_in_client.get("/_admin/api/tokens/9999/logs")
    assert response.status_code == 404


async def test_token_datetime_fields_are_utc_aware(logged_in_client: AsyncClient) -> None:
    expires_at = (datetime.now(UTC) + timedelta(days=1)).isoformat()

    create_response = await logged_in_client.post(
        "/_admin/api/tokens", json={"name": "t1", "expires_at": expires_at}
    )
    assert create_response.status_code == 201
    created = create_response.json()
    _assert_utc_aware(created["created_at"])
    _assert_utc_aware(created["expires_at"])
    token_id = created["id"]

    list_response = await logged_in_client.get("/_admin/api/tokens")
    listed = list_response.json()[0]
    _assert_utc_aware(listed["created_at"])
    _assert_utc_aware(listed["expires_at"])

    detail_response = await logged_in_client.get(f"/_admin/api/tokens/{token_id}")
    detail = detail_response.json()
    _assert_utc_aware(detail["created_at"])
    _assert_utc_aware(detail["expires_at"])

    revoke_response = await logged_in_client.post(f"/_admin/api/tokens/{token_id}/revoke")
    revoked = revoke_response.json()
    _assert_utc_aware(revoked["created_at"])
    _assert_utc_aware(revoked["revoked_at"])
