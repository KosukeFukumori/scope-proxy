from httpx import AsyncClient
from sqlmodel import Session, select

from app.models.operation import Operation
from app.models.token import TokenPermission


async def test_get_backend_config_requires_authentication(client: AsyncClient) -> None:
    response = await client.get("/_admin/api/backend-config")
    assert response.status_code == 401


async def test_get_backend_config_not_set(logged_in_client: AsyncClient) -> None:
    response = await logged_in_client.get("/_admin/api/backend-config")
    assert response.status_code == 404


async def test_upsert_and_get_backend_config(logged_in_client: AsyncClient) -> None:
    payload = {
        "endpoint_url": "https://api.example.com",
        "openapi_url": "https://api.example.com/openapi.json",
    }
    response = await logged_in_client.put("/_admin/api/backend-config", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["endpoint_url"] == "https://api.example.com/"
    assert body["openapi_url"] == "https://api.example.com/openapi.json"
    assert body["last_fetched_at"] is None

    response = await logged_in_client.get("/_admin/api/backend-config")
    assert response.status_code == 200
    assert response.json()["openapi_url"] == "https://api.example.com/openapi.json"


async def test_upsert_backend_config_updates_existing(logged_in_client: AsyncClient) -> None:
    first = {
        "endpoint_url": "https://api.example.com",
        "openapi_url": "https://api.example.com/openapi.json",
    }
    await logged_in_client.put("/_admin/api/backend-config", json=first)

    second = {
        "endpoint_url": "https://api2.example.com",
        "openapi_url": "https://api2.example.com/openapi.json",
    }
    response = await logged_in_client.put("/_admin/api/backend-config", json=second)
    assert response.status_code == 200
    assert response.json()["endpoint_url"] == "https://api2.example.com/"


async def _seed_operation_and_permission(session: Session, logged_in_client: AsyncClient) -> None:
    session.add(Operation(operation_id="op1", method="GET", path="/users", is_active=True))
    session.commit()
    response = await logged_in_client.post("/_admin/api/tokens", json={"name": "t1", "operation_ids": ["op1"]})
    assert response.status_code == 201


async def test_url_change_resets_operations_and_permissions(
    logged_in_client: AsyncClient, session: Session
) -> None:
    config = {
        "endpoint_url": "https://api.example.com",
        "openapi_url": "https://api.example.com/openapi.json",
    }
    await logged_in_client.put("/_admin/api/backend-config", json=config)
    await _seed_operation_and_permission(session, logged_in_client)

    changed = {
        "endpoint_url": "https://api2.example.com",
        "openapi_url": "https://api2.example.com/openapi.json",
    }
    response = await logged_in_client.put("/_admin/api/backend-config", json=changed)
    assert response.status_code == 200
    assert response.json()["last_fetched_at"] is None

    # Permissions must never carry over to a different backend, even if it
    # exposes operations with identical hash ids.
    assert session.exec(select(Operation)).all() == []
    assert session.exec(select(TokenPermission)).all() == []


async def test_saving_unchanged_urls_keeps_operations_and_permissions(
    logged_in_client: AsyncClient, session: Session
) -> None:
    config = {
        "endpoint_url": "https://api.example.com",
        "openapi_url": "https://api.example.com/openapi.json",
    }
    await logged_in_client.put("/_admin/api/backend-config", json=config)
    await _seed_operation_and_permission(session, logged_in_client)

    response = await logged_in_client.put("/_admin/api/backend-config", json=config)
    assert response.status_code == 200

    assert len(session.exec(select(Operation)).all()) == 1
    assert len(session.exec(select(TokenPermission)).all()) == 1
