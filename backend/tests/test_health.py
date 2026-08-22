from httpx import AsyncClient


async def test_health_does_not_require_authentication(client: AsyncClient) -> None:
    response = await client.get("/_admin/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
