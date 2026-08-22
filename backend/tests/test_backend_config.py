from collections.abc import Generator

import pytest
from httpx import AsyncClient
from sqlmodel import Session, select

from app.config import settings
from app.models.operation import Operation
from app.models.token import TokenPermission
from app.routers.backend_config import apply_env_config_overrides


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


async def test_upsert_backend_config_without_sync_interval_falls_back_to_env_default(
    logged_in_client: AsyncClient,
) -> None:
    payload = {
        "endpoint_url": "https://api.example.com",
        "openapi_url": "https://api.example.com/openapi.json",
    }
    response = await logged_in_client.put("/_admin/api/backend-config", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["schema_sync_interval_seconds"] is None
    # settings.schema_sync_interval_seconds defaults to 0 (disabled) in the test app.
    assert body["effective_schema_sync_interval_seconds"] == 0


async def test_upsert_backend_config_with_sync_interval_overrides_env_default(
    logged_in_client: AsyncClient,
) -> None:
    payload = {
        "endpoint_url": "https://api.example.com",
        "openapi_url": "https://api.example.com/openapi.json",
        "schema_sync_interval_seconds": 120,
    }
    response = await logged_in_client.put("/_admin/api/backend-config", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["schema_sync_interval_seconds"] == 120
    assert body["effective_schema_sync_interval_seconds"] == 120

    response = await logged_in_client.get("/_admin/api/backend-config")
    assert response.json()["effective_schema_sync_interval_seconds"] == 120


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


@pytest.fixture
def clear_env_preset() -> Generator[None]:
    """settings is a process-wide singleton; make sure no test leaks its overrides."""
    original_endpoint_url = settings.endpoint_url
    original_openapi_url = settings.openapi_url
    yield
    settings.endpoint_url = original_endpoint_url
    settings.openapi_url = original_openapi_url


async def test_env_preset_defaults_to_unset(logged_in_client: AsyncClient, clear_env_preset: None) -> None:
    response = await logged_in_client.get("/_admin/api/backend-config/env-preset")
    assert response.status_code == 200
    assert response.json() == {"endpoint_url": None, "openapi_url": None}


async def test_env_preset_reports_locked_fields(logged_in_client: AsyncClient, clear_env_preset: None) -> None:
    settings.endpoint_url = "https://locked.example.com"

    preset_response = await logged_in_client.get("/_admin/api/backend-config/env-preset")
    assert preset_response.json() == {"endpoint_url": "https://locked.example.com", "openapi_url": None}

    await logged_in_client.put(
        "/_admin/api/backend-config",
        json={
            "endpoint_url": "https://ignored.example.com",
            "openapi_url": "https://api.example.com/openapi.json",
        },
    )
    response = await logged_in_client.get("/_admin/api/backend-config")
    body = response.json()
    assert body["endpoint_url_locked"] is True
    assert body["openapi_url_locked"] is False


async def test_env_locked_endpoint_url_overrides_payload_on_upsert(
    logged_in_client: AsyncClient, clear_env_preset: None
) -> None:
    settings.endpoint_url = "https://locked.example.com"

    response = await logged_in_client.put(
        "/_admin/api/backend-config",
        json={
            "endpoint_url": "https://attempted-override.example.com",
            "openapi_url": "https://api.example.com/openapi.json",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["endpoint_url"] == "https://locked.example.com"
    assert body["openapi_url"] == "https://api.example.com/openapi.json"


async def test_apply_env_config_overrides_creates_row_when_both_urls_preset(
    session: Session, clear_env_preset: None
) -> None:
    settings.endpoint_url = "https://locked.example.com"
    settings.openapi_url = "https://locked.example.com/openapi.json"

    apply_env_config_overrides(session)

    from app.models.backend_config import BackendConfig

    config = session.get(BackendConfig, 1)
    assert config is not None
    assert config.endpoint_url == "https://locked.example.com"
    assert config.openapi_url == "https://locked.example.com/openapi.json"


async def test_apply_env_config_overrides_skips_row_creation_when_only_one_url_preset(
    session: Session, clear_env_preset: None
) -> None:
    settings.endpoint_url = "https://locked.example.com"

    apply_env_config_overrides(session)

    from app.models.backend_config import BackendConfig

    assert session.get(BackendConfig, 1) is None


async def test_apply_env_config_overrides_resets_operations_on_url_change(
    logged_in_client: AsyncClient, session: Session, clear_env_preset: None
) -> None:
    config = {
        "endpoint_url": "https://api.example.com",
        "openapi_url": "https://api.example.com/openapi.json",
    }
    await logged_in_client.put("/_admin/api/backend-config", json=config)
    await _seed_operation_and_permission(session, logged_in_client)

    settings.endpoint_url = "https://api2.example.com"
    apply_env_config_overrides(session)

    from app.models.backend_config import BackendConfig

    stored = session.get(BackendConfig, 1)
    assert stored is not None
    assert stored.endpoint_url == "https://api2.example.com"
    assert stored.last_fetched_at is None
    assert session.exec(select(Operation)).all() == []
    assert session.exec(select(TokenPermission)).all() == []
