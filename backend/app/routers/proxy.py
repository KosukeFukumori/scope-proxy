from datetime import UTC, datetime

import httpx
from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlmodel import select
from starlette.background import BackgroundTask
from starlette.datastructures import Headers

from app.deps import SessionDep
from app.models.backend_config import BackendConfig
from app.models.operation import Operation
from app.models.token import Token, TokenPermission
from app.services.operation_matcher import get_cached_operation_matcher
from app.services.token_service import hash_token

router = APIRouter(tags=["proxy"])

HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
}

REQUEST_ONLY_STRIPPED_HEADERS = {"host", "authorization", "content-length"}
RESPONSE_ONLY_STRIPPED_HEADERS = {"content-length"}


def strip_hop_by_hop(headers: Headers | httpx.Headers, extra: set[str]) -> list[tuple[str, str]]:
    excluded = HOP_BY_HOP_HEADERS | extra
    return [(key, value) for key, value in headers.items() if key.lower() not in excluded]


def _as_aware_utc(value: datetime) -> datetime:
    """SQLite doesn't preserve tzinfo, so treat naive values as UTC."""
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


async def _authenticate_token(session: SessionDep, authorization: str | None) -> Token:
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    raw_token = authorization.removeprefix("Bearer ").strip()
    token = session.exec(select(Token).where(Token.token_hash == hash_token(raw_token))).first()
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    now = datetime.now(UTC)
    if token.revoked_at is not None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked")
    if token.expires_at is not None and _as_aware_utc(token.expires_at) <= now:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")

    return token


def _resolve_operation(session: SessionDep, method: str, path: str) -> Operation:
    all_operations = list(session.exec(select(Operation)).all())
    matcher = get_cached_operation_matcher(all_operations)
    operation_id = matcher.match(method, path)
    if operation_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    # Look up in the already-fetched list instead of issuing another query.
    operations_by_id = {op.operation_id: op for op in all_operations}
    operation = operations_by_id.get(operation_id)
    if operation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return operation


def _ensure_permission(session: SessionDep, token: Token, operation: Operation) -> None:
    has_permission = session.exec(
        select(TokenPermission).where(
            TokenPermission.token_id == token.id,
            TokenPermission.operation_id == operation.operation_id,
        )
    ).first()
    if not operation.is_active or has_permission is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)


@router.api_route(
    "/{full_path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
    include_in_schema=False,
)
async def proxy(full_path: str, request: Request, session: SessionDep) -> StreamingResponse:
    token = await _authenticate_token(session, request.headers.get("authorization"))

    operation = _resolve_operation(session, request.method, request.url.path)
    _ensure_permission(session, token, operation)

    backend_config = session.get(BackendConfig, 1)
    if backend_config is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Backend is not configured")

    target_url = httpx.URL(backend_config.endpoint_url).copy_with(
        path=request.url.path,
        query=request.url.query.encode(),
    )

    http_client: httpx.AsyncClient = request.app.state.http_client
    upstream_request = http_client.build_request(
        method=request.method,
        url=target_url,
        headers=strip_hop_by_hop(request.headers, REQUEST_ONLY_STRIPPED_HEADERS),
        content=request.stream(),
    )
    try:
        upstream_response = await http_client.send(upstream_request, stream=True)
    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail="Upstream request timed out"
        ) from exc
    except httpx.ConnectError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail="Failed to connect to upstream backend"
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail="Upstream backend request failed"
        ) from exc

    token.last_used_at = datetime.now(UTC)
    session.add(token)
    session.commit()

    return StreamingResponse(
        upstream_response.aiter_raw(),
        status_code=upstream_response.status_code,
        headers=dict(strip_hop_by_hop(upstream_response.headers, RESPONSE_ONLY_STRIPPED_HEADERS)),
        background=BackgroundTask(upstream_response.aclose),
    )
