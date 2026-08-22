import asyncio
import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime

import httpx
from sqlalchemy import Engine, desc
from sqlmodel import Session, select

from app.models.backend_config import BackendConfig
from app.models.operation import Operation
from app.models.schema_snapshot import SchemaSnapshot

logger = logging.getLogger("scope_proxy")

ADMIN_PATH_PREFIX = "/_admin"

# BackendConfig.id of the single backend configuration record used by this app.
BACKEND_CONFIG_ID = 1


@dataclass
class ExtractedOperation:
    operation_id: str
    method: str
    path: str
    summary: str | None


@dataclass
class SyncResult:
    added: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    skipped_admin_conflict: list[str] = field(default_factory=list)

    def to_diff_summary(self) -> str:
        return json.dumps(
            {
                "added": self.added,
                "updated": self.updated,
                "removed": self.removed,
                "skipped_admin_conflict": self.skipped_admin_conflict,
            },
            sort_keys=True,
        )


def _extract_operations(spec: dict) -> list[ExtractedOperation]:
    operations: list[ExtractedOperation] = []
    paths = spec.get("paths", {})
    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue
        for method, operation in path_item.items():
            if method.lower() not in {"get", "post", "put", "patch", "delete", "options", "head"}:
                continue
            if not isinstance(operation, dict):
                continue
            operation_id = operation.get("operationId") or f"{method.lower()}_{path}"
            operations.append(
                ExtractedOperation(
                    operation_id=operation_id,
                    method=method.upper(),
                    path=path,
                    summary=operation.get("summary"),
                )
            )
    return operations


async def fetch_openapi_spec(openapi_url: str) -> dict:
    async with httpx.AsyncClient() as http_client:
        response = await http_client.get(openapi_url)
        response.raise_for_status()
        return response.json()


def sync_operations(session: Session, spec: dict) -> SyncResult:
    """Reconcile the operations table with the fetched OpenAPI spec.

    - New operationId -> added with is_active=True. Permissions are not granted automatically
    - Still present -> method/path/summary updated, is_active reset to True
    - No longer present -> is_active set to False (token_permissions are not deleted)
    - Paths starting with /_admin are excluded from proxying since they'd conflict with the admin UI
    """
    extracted = _extract_operations(spec)
    result = SyncResult()

    seen_ids: set[str] = set()
    for item in extracted:
        if item.path.startswith(ADMIN_PATH_PREFIX):
            result.skipped_admin_conflict.append(item.operation_id)
            continue

        seen_ids.add(item.operation_id)
        existing = session.get(Operation, item.operation_id)
        if existing is None:
            session.add(
                Operation(
                    operation_id=item.operation_id,
                    method=item.method,
                    path=item.path,
                    summary=item.summary,
                    is_active=True,
                )
            )
            result.added.append(item.operation_id)
        else:
            existing.method = item.method
            existing.path = item.path
            existing.summary = item.summary
            existing.is_active = True
            session.add(existing)
            result.updated.append(item.operation_id)

    all_operations = session.exec(select(Operation)).all()
    for operation in all_operations:
        if operation.operation_id not in seen_ids and operation.is_active:
            operation.is_active = False
            session.add(operation)
            result.removed.append(operation.operation_id)

    return result


def _get_latest_snapshot(session: Session) -> SchemaSnapshot | None:
    # sqlmodel field access is statically typed as `datetime`, not a Column, so pyright
    # cannot see that this is actually a SQLAlchemy InstrumentedAttribute at runtime.
    statement = select(SchemaSnapshot).order_by(desc(SchemaSnapshot.fetched_at)).limit(1)  # type: ignore[arg-type]
    return session.exec(statement).first()


async def refresh_backend_schema(session: Session, backend_config: BackendConfig) -> SchemaSnapshot:
    """Fetch the upstream OpenAPI spec, reconcile operations, and record a snapshot.

    Also records the outcome (success/error) on backend_config so the dashboard can
    show whether the most recent sync attempt (manual or scheduled) succeeded, regardless
    of whether the failure happened during the fetch or afterwards.
    """
    try:
        spec = await fetch_openapi_spec(backend_config.openapi_url)
        spec_hash = hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest()

        result = sync_operations(session, spec)

        backend_config.last_fetched_at = datetime.now(UTC)
        backend_config.last_sync_status = "success"
        backend_config.last_sync_error = None
        session.add(backend_config)

        latest_snapshot = _get_latest_snapshot(session)
        if latest_snapshot is not None and latest_snapshot.spec_hash == spec_hash:
            # Spec is unchanged since the last snapshot: avoid piling up "no change" rows,
            # which would otherwise flood the history once periodic sync is introduced.
            session.commit()
            session.refresh(latest_snapshot)
            return latest_snapshot

        snapshot = SchemaSnapshot(spec_hash=spec_hash, diff_summary=result.to_diff_summary())
        session.add(snapshot)

        session.commit()
        session.refresh(snapshot)
        return snapshot
    except Exception as exc:
        backend_config.last_sync_status = "error"
        backend_config.last_sync_error = str(exc)[:2000]
        session.add(backend_config)
        session.commit()
        raise


async def run_scheduled_sync(engine: Engine) -> None:
    """Run a single scheduled sync attempt against the singleton backend config, if configured.

    Failures are logged as warnings (and recorded on backend_config via refresh_backend_schema)
    instead of being raised, so the periodic loop keeps running.
    """
    with Session(engine) as session:
        backend_config = session.get(BackendConfig, BACKEND_CONFIG_ID)
        if backend_config is None:
            logger.debug("Skipping scheduled schema sync: backend config is not set")
            return

        try:
            await refresh_backend_schema(session, backend_config)
        except Exception:
            logger.warning("Scheduled schema sync failed for %s", backend_config.openapi_url, exc_info=True)


async def schema_sync_loop(engine: Engine, interval_seconds: float) -> None:
    """Periodically run schema sync every interval_seconds until the task is cancelled.

    Intended to be started as an asyncio task from the FastAPI lifespan and cancelled on shutdown.
    """
    while True:
        await asyncio.sleep(interval_seconds)
        try:
            await run_scheduled_sync(engine)
        except asyncio.CancelledError:
            raise
        except Exception:
            # Defensive: run_scheduled_sync already handles sync failures internally, but this
            # ensures a truly unexpected error (e.g. a DB connectivity issue) never kills the loop.
            logger.exception("Unexpected error in schema sync loop")
