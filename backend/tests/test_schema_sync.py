import json
from datetime import datetime, timedelta

import respx
from httpx import AsyncClient, Response
from sqlmodel import Session, select

from app.models.operation import Operation
from app.models.token import TokenPermission
from app.services.schema_sync import compute_operation_id


def _assert_utc_aware(value: str) -> None:
    """Assert a serialized datetime string carries a UTC offset (`+00:00` / `Z`)."""
    parsed = datetime.fromisoformat(value)
    assert parsed.tzinfo is not None
    assert parsed.utcoffset() == timedelta(0)

OPENAPI_URL = "https://api.example.com/openapi.json"

# Hash-based operation ids for the specs below.
LIST_USERS_ID = compute_operation_id("GET", "/users", "listUsers")
GET_USER_ID = compute_operation_id("GET", "/users/{id}", "getUser")
CREATE_USER_ID = compute_operation_id("POST", "/users", "createUser")

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
    assert ids == {LIST_USERS_ID, GET_USER_ID}
    assert all(op.is_active for op in operations)
    assert {op.openapi_operation_id for op in operations} == {"listUsers", "getUser"}

    body = response.json()
    # Diff of this run: human-readable "METHOD /path" labels.
    diff = json.loads(body["diff_summary"])
    assert sorted(diff["added"]) == ["GET /users", "GET /users/{id}"]
    assert json.loads(body["snapshot"]["diff_summary"]) == diff
    _assert_utc_aware(body["snapshot"]["fetched_at"])

    config_response = await logged_in_client.get("/_admin/api/backend-config")
    _assert_utc_aware(config_response.json()["last_fetched_at"])


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
    assert diff["added"] == ["POST /users"]
    assert diff["updated"] == ["GET /users"]
    assert diff["removed"] == ["GET /users/{id}"]
    assert diff["skipped_admin_conflict"] == ["GET /_admin/api/tokens"]

    operations = {op.operation_id: op for op in session.exec(select(Operation)).all()}
    assert operations[GET_USER_ID].is_active is False
    assert operations[LIST_USERS_ID].summary == "list all users"
    assert compute_operation_id("GET", "/_admin/api/tokens", "adminTokens") not in operations


@respx.mock
async def test_refresh_keeps_token_permissions_for_deactivated_operation(
    logged_in_client: AsyncClient, session: Session
) -> None:
    await _set_backend_config(logged_in_client)
    respx.get(OPENAPI_URL).mock(return_value=Response(200, json=SPEC_V1))
    await logged_in_client.post("/_admin/api/backend-config/refresh")

    create_response = await logged_in_client.post(
        "/_admin/api/tokens", json={"name": "t1", "operation_ids": [GET_USER_ID]}
    )
    token_id = create_response.json()["id"]

    respx.get(OPENAPI_URL).mock(return_value=Response(200, json=SPEC_V2))
    await logged_in_client.post("/_admin/api/backend-config/refresh")

    permissions = session.exec(select(TokenPermission).where(TokenPermission.token_id == token_id)).all()
    assert len(permissions) == 1
    assert permissions[0].operation_id == GET_USER_ID


@respx.mock
async def test_operation_id_changes_when_openapi_id_reused_for_different_path(
    logged_in_client: AsyncClient, session: Session
) -> None:
    """Reusing an operationId for a different method/path must yield a different
    hash id, so permissions granted to the old endpoint never carry over."""
    await _set_backend_config(logged_in_client)
    respx.get(OPENAPI_URL).mock(return_value=Response(200, json=SPEC_V1))
    await logged_in_client.post("/_admin/api/backend-config/refresh")

    reused_spec = {
        "openapi": "3.0.0",
        "info": {"title": "t", "version": "1"},
        "paths": {
            "/accounts/{id}": {
                "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}],
                "delete": {"operationId": "getUser", "responses": {"200": {"description": "ok"}}},
            },
        },
    }
    respx.get(OPENAPI_URL).mock(return_value=Response(200, json=reused_spec))
    await logged_in_client.post("/_admin/api/backend-config/refresh")

    operations = {op.operation_id: op for op in session.exec(select(Operation)).all()}
    reused_id = compute_operation_id("DELETE", "/accounts/{id}", "getUser")
    assert reused_id != GET_USER_ID
    assert operations[GET_USER_ID].is_active is False
    assert operations[reused_id].is_active is True


@respx.mock
async def test_duplicate_openapi_ids_on_different_paths_both_registered(
    logged_in_client: AsyncClient, session: Session
) -> None:
    """A spec-violating duplicate operationId must not silently merge two endpoints."""
    await _set_backend_config(logged_in_client)
    duplicate_spec = {
        "openapi": "3.0.0",
        "info": {"title": "t", "version": "1"},
        "paths": {
            "/a": {"get": {"operationId": "dup", "responses": {"200": {"description": "ok"}}}},
            "/b": {"get": {"operationId": "dup", "responses": {"200": {"description": "ok"}}}},
        },
    }
    respx.get(OPENAPI_URL).mock(return_value=Response(200, json=duplicate_spec))
    await logged_in_client.post("/_admin/api/backend-config/refresh")

    operations = session.exec(select(Operation)).all()
    assert {op.path for op in operations} == {"/a", "/b"}
    assert len({op.operation_id for op in operations}) == 2


@respx.mock
async def test_list_operations_filter_by_is_active(logged_in_client: AsyncClient) -> None:
    await _set_backend_config(logged_in_client)
    respx.get(OPENAPI_URL).mock(return_value=Response(200, json=SPEC_V1))
    await logged_in_client.post("/_admin/api/backend-config/refresh")
    respx.get(OPENAPI_URL).mock(return_value=Response(200, json=SPEC_V2))
    await logged_in_client.post("/_admin/api/backend-config/refresh")

    active_response = await logged_in_client.get("/_admin/api/operations", params={"is_active": "true"})
    inactive_response = await logged_in_client.get("/_admin/api/operations", params={"is_active": "false"})

    assert {op["operation_id"] for op in active_response.json()} == {LIST_USERS_ID, CREATE_USER_ID}
    assert {op["openapi_operation_id"] for op in active_response.json()} == {"listUsers", "createUser"}
    assert {op["operation_id"] for op in inactive_response.json()} == {GET_USER_ID}


@respx.mock
async def test_schema_snapshots_history(logged_in_client: AsyncClient) -> None:
    await _set_backend_config(logged_in_client)
    respx.get(OPENAPI_URL).mock(return_value=Response(200, json=SPEC_V1))
    await logged_in_client.post("/_admin/api/backend-config/refresh")

    response = await logged_in_client.get("/_admin/api/schema-snapshots")
    assert response.status_code == 200
    assert len(response.json()) == 1


@respx.mock
async def test_refresh_skips_snapshot_when_spec_unchanged(logged_in_client: AsyncClient, session: Session) -> None:
    await _set_backend_config(logged_in_client)
    respx.get(OPENAPI_URL).mock(return_value=Response(200, json=SPEC_V1))

    first_response = await logged_in_client.post("/_admin/api/backend-config/refresh")
    second_response = await logged_in_client.post("/_admin/api/backend-config/refresh")

    assert first_response.json()["snapshot"]["id"] == second_response.json()["snapshot"]["id"]
    # The second run made no changes, so its own diff must be empty even though
    # the returned (deduplicated) snapshot still carries the first run's diff.
    second_diff = json.loads(second_response.json()["diff_summary"])
    assert all(value == [] for value in second_diff.values())

    snapshots_response = await logged_in_client.get("/_admin/api/schema-snapshots")
    assert len(snapshots_response.json()) == 1
