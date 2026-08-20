import json

import respx
from httpx import AsyncClient, Response
from sqlmodel import Session, select

from app.models.operation import Operation
from app.models.token import TokenPermission

OPENAPI_URL = "https://api.example.com/openapi.json"

SPEC_V1 = {
    "openapi": "3.0.0",
    "info": {"title": "t", "version": "1"},
    "paths": {
        "/users": {
            "get": {"operationId": "listUsers", "summary": "list users", "responses": {"200": {"description": "ok"}}}
        },
        "/users/{id}": {
            "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}],
            "get": {"operationId": "getUser", "responses": {"200": {"description": "ok"}}},
        },
    },
}

SPEC_V2 = {
    "openapi": "3.0.0",
    "info": {"title": "t", "version": "1"},
    "paths": {
        "/users": {
            "get": {
                "operationId": "listUsers",
                "summary": "list all users",
                "responses": {"200": {"description": "ok"}},
            },
            "post": {"operationId": "createUser", "responses": {"200": {"description": "ok"}}},
        },
        "/_admin/api/tokens": {"get": {"operationId": "adminTokens", "responses": {"200": {"description": "ok"}}}},
    },
}


async def _set_backend_config(client: AsyncClient) -> None:
    await client.put(
        "/_admin/api/backend-config",
        json={"endpoint_url": "https://api.example.com", "openapi_url": OPENAPI_URL},
    )


@respx.mock
async def test_refresh_adds_new_operations(logged_in_client: AsyncClient, session: Session) -> None:
    await _set_backend_config(logged_in_client)
    respx.get(OPENAPI_URL).mock(return_value=Response(200, json=SPEC_V1))

    response = await logged_in_client.post("/_admin/api/backend-config/refresh")
    assert response.status_code == 200

    operations = session.exec(select(Operation)).all()
    ids = {op.operation_id for op in operations}
    assert ids == {"listUsers", "getUser"}
    assert all(op.is_active for op in operations)

    diff = json.loads(response.json()["diff_summary"])
    assert sorted(diff["added"]) == ["getUser", "listUsers"]


@respx.mock
async def test_refresh_updates_and_removes_and_excludes_admin_paths(
    logged_in_client: AsyncClient, session: Session
) -> None:
    await _set_backend_config(logged_in_client)
    respx.get(OPENAPI_URL).mock(return_value=Response(200, json=SPEC_V1))
    await logged_in_client.post("/_admin/api/backend-config/refresh")

    respx.get(OPENAPI_URL).mock(return_value=Response(200, json=SPEC_V2))
    response = await logged_in_client.post("/_admin/api/backend-config/refresh")
    assert response.status_code == 200

    diff = json.loads(response.json()["diff_summary"])
    assert diff["added"] == ["createUser"]
    assert diff["updated"] == ["listUsers"]
    assert diff["removed"] == ["getUser"]
    assert diff["skipped_admin_conflict"] == ["adminTokens"]

    operations = {op.operation_id: op for op in session.exec(select(Operation)).all()}
    assert operations["getUser"].is_active is False
    assert operations["listUsers"].summary == "list all users"
    assert "adminTokens" not in operations


@respx.mock
async def test_refresh_keeps_token_permissions_for_deactivated_operation(
    logged_in_client: AsyncClient, session: Session
) -> None:
    await _set_backend_config(logged_in_client)
    respx.get(OPENAPI_URL).mock(return_value=Response(200, json=SPEC_V1))
    await logged_in_client.post("/_admin/api/backend-config/refresh")

    create_response = await logged_in_client.post(
        "/_admin/api/tokens", json={"name": "t1", "operation_ids": ["getUser"]}
    )
    token_id = create_response.json()["id"]

    respx.get(OPENAPI_URL).mock(return_value=Response(200, json=SPEC_V2))
    await logged_in_client.post("/_admin/api/backend-config/refresh")

    permissions = session.exec(select(TokenPermission).where(TokenPermission.token_id == token_id)).all()
    assert len(permissions) == 1
    assert permissions[0].operation_id == "getUser"


@respx.mock
async def test_list_operations_filter_by_is_active(logged_in_client: AsyncClient) -> None:
    await _set_backend_config(logged_in_client)
    respx.get(OPENAPI_URL).mock(return_value=Response(200, json=SPEC_V1))
    await logged_in_client.post("/_admin/api/backend-config/refresh")
    respx.get(OPENAPI_URL).mock(return_value=Response(200, json=SPEC_V2))
    await logged_in_client.post("/_admin/api/backend-config/refresh")

    active_response = await logged_in_client.get("/_admin/api/operations", params={"is_active": "true"})
    inactive_response = await logged_in_client.get("/_admin/api/operations", params={"is_active": "false"})

    assert {op["operation_id"] for op in active_response.json()} == {"listUsers", "createUser"}
    assert {op["operation_id"] for op in inactive_response.json()} == {"getUser"}


@respx.mock
async def test_schema_snapshots_history(logged_in_client: AsyncClient) -> None:
    await _set_backend_config(logged_in_client)
    respx.get(OPENAPI_URL).mock(return_value=Response(200, json=SPEC_V1))
    await logged_in_client.post("/_admin/api/backend-config/refresh")

    response = await logged_in_client.get("/_admin/api/schema-snapshots")
    assert response.status_code == 200
    assert len(response.json()) == 1
