from datetime import UTC, datetime, timedelta

import respx
from httpx import AsyncClient, Response
from sqlmodel import Session, select

from app.models.backend_config import BackendConfig
from app.models.operation import Operation
from app.models.token import Token, TokenPermission
from app.services.token_service import generate_token

BACKEND_URL = "https://api.example.com"


def _setup_backend(session: Session) -> None:
    session.add(BackendConfig(id=1, endpoint_url=BACKEND_URL, openapi_url=f"{BACKEND_URL}/openapi.json"))
    session.add(Operation(operation_id="getUser", method="GET", path="/users/1", is_active=True))
    session.add(Operation(operation_id="inactiveOp", method="GET", path="/inactive", is_active=False))
    session.commit()


def _create_token(session: Session, *, operation_ids: list[str], revoked: bool = False, expired: bool = False) -> str:
    raw, token_hash = generate_token()
    token = Token(
        user_id=1,
        name="t",
        token_hash=token_hash,
        revoked_at=datetime.now(UTC) if revoked else None,
        expires_at=(datetime.now(UTC) - timedelta(days=1)) if expired else None,
    )
    session.add(token)
    session.commit()
    session.refresh(token)
    for operation_id in operation_ids:
        session.add(TokenPermission(token_id=token.id, operation_id=operation_id))
    session.commit()
    return raw


async def test_missing_authorization_header(client: AsyncClient, session: Session) -> None:
    _setup_backend(session)
    response = await client.get("/users/1")
    assert response.status_code == 401


async def test_invalid_token(client: AsyncClient, session: Session) -> None:
    _setup_backend(session)
    response = await client.get("/users/1", headers={"Authorization": "Bearer not-a-real-token"})
    assert response.status_code == 401


async def test_revoked_token(client: AsyncClient, session: Session) -> None:
    _setup_backend(session)
    raw = _create_token(session, operation_ids=["getUser"], revoked=True)
    response = await client.get("/users/1", headers={"Authorization": f"Bearer {raw}"})
    assert response.status_code == 401


async def test_expired_token(client: AsyncClient, session: Session) -> None:
    _setup_backend(session)
    raw = _create_token(session, operation_ids=["getUser"], expired=True)
    response = await client.get("/users/1", headers={"Authorization": f"Bearer {raw}"})
    assert response.status_code == 401


async def test_unmatched_path_returns_404(client: AsyncClient, session: Session) -> None:
    _setup_backend(session)
    raw = _create_token(session, operation_ids=["getUser"])
    response = await client.get("/no-such-path", headers={"Authorization": f"Bearer {raw}"})
    assert response.status_code == 404


async def test_inactive_operation_returns_403(client: AsyncClient, session: Session) -> None:
    _setup_backend(session)
    raw = _create_token(session, operation_ids=["inactiveOp"])
    response = await client.get("/inactive", headers={"Authorization": f"Bearer {raw}"})
    assert response.status_code == 403


async def test_no_permission_returns_403(client: AsyncClient, session: Session) -> None:
    _setup_backend(session)
    raw = _create_token(session, operation_ids=[])
    response = await client.get("/users/1", headers={"Authorization": f"Bearer {raw}"})
    assert response.status_code == 403


@respx.mock
async def test_authorized_request_is_forwarded(client: AsyncClient, session: Session) -> None:
    _setup_backend(session)
    raw = _create_token(session, operation_ids=["getUser"])

    route = respx.get(f"{BACKEND_URL}/users/1").mock(
        return_value=Response(200, json={"id": 1, "name": "Alice"}, headers={"X-Custom": "value"})
    )

    response = await client.get(
        "/users/1",
        headers={"Authorization": "Bearer " + raw, "X-Client": "test"},
    )

    assert response.status_code == 200
    assert response.json() == {"id": 1, "name": "Alice"}
    assert response.headers["x-custom"] == "value"

    upstream_request = route.calls.last.request
    assert "authorization" not in upstream_request.headers
    assert upstream_request.headers["x-client"] == "test"

    token = session.exec(select(Token)).first()
    assert token.last_used_at is not None


@respx.mock
async def test_query_string_is_forwarded(client: AsyncClient, session: Session) -> None:
    _setup_backend(session)
    raw = _create_token(session, operation_ids=["getUser"])

    route = respx.get(f"{BACKEND_URL}/users/1", params={"verbose": "true"}).mock(return_value=Response(200, json={}))

    response = await client.get("/users/1?verbose=true", headers={"Authorization": f"Bearer {raw}"})

    assert response.status_code == 200
    assert route.calls.last.request.url.params["verbose"] == "true"


async def test_backend_not_configured_returns_503(client: AsyncClient, session: Session) -> None:
    session.add(Operation(operation_id="getUser", method="GET", path="/users/1", is_active=True))
    session.commit()
    raw = _create_token(session, operation_ids=["getUser"])

    response = await client.get("/users/1", headers={"Authorization": f"Bearer {raw}"})
    assert response.status_code == 503
