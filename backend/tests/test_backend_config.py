from httpx import AsyncClient


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
