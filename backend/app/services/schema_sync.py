import asyncio
import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime

import httpx
from sqlalchemy import Engine, desc
from sqlmodel import Session, select

from app.config import settings
from app.models.backend_config import BackendConfig
from app.models.operation import Operation
from app.models.schema_snapshot import SchemaSnapshot

logger = logging.getLogger("scope_proxy")

ADMIN_PATH_PREFIX = "/_admin"

# BackendConfig.id of the single backend configuration record used by this app.
BACKEND_CONFIG_ID = 1

# How often the background loop checks whether a sync is due. Kept independent of the
# configured sync interval so a change made from the GUI takes effect within one tick
# instead of requiring an app restart.
SCHEDULER_TICK_SECONDS = 30

# Length (in hex chars) of the truncated sha256 digest used as operation_id.
# 32 hex chars = 128 bits, plenty to avoid collisions.
OPERATION_ID_LENGTH = 32


def effective_sync_interval_seconds(backend_config: BackendConfig) -> int:
    """Resolve the interval actually in effect: the GUI override if set, otherwise the env var default."""
    if backend_config.schema_sync_interval_seconds is not None:
        return backend_config.schema_sync_interval_seconds
    return settings.schema_sync_interval_seconds


def compute_operation_id(method: str, path: str, openapi_operation_id: str | None) -> str:
    """Derive the stable operation identity from method, path and OpenAPI operationId.

    Permissions survive a schema refresh only while all three components stay
    identical; changing any of them yields a new id, so stale permissions are
    never inherited by a different endpoint (fail-safe).
    """
    material = f"{method.upper()} {path} {openapi_operation_id or ''}"
    return hashlib.sha256(material.encode()).hexdigest()[:OPERATION_ID_LENGTH]


@dataclass
class ExtractedOperation:
    operation_id: str
    method: str
    path: str
    openapi_operation_id: str | None
    summary: str | None

    @property
    def label(self) -> str:
        """Human-readable identifier used in diff summaries shown in the admin UI."""
        return f"{self.method} {self.path}"


@dataclass
class SyncResult:
    """Lists hold human-readable operation labels ("METHOD /path"), not hash ids."""

    added: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    skipped_admin_conflict: list[str] = field(default_factory=list)

    def has_changes(self) -> bool:
        return bool(self.added or self.updated or self.removed or self.skipped_admin_conflict)

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
            openapi_operation_id = operation.get("operationId")
            operations.append(
                ExtractedOperation(
                    operation_id=compute_operation_id(method, path, openapi_operation_id),
                    method=method.upper(),
                    path=path,
                    openapi_operation_id=openapi_operation_id,
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

    Identity is the (method, path, operationId) hash, so:
    - New hash -> added with is_active=True. Permissions are not granted automatically
    - Same hash -> summary refreshed; reported as updated only if something actually changed
    - Hash no longer present -> is_active set to False (token_permissions are not deleted;
      they can never leak to a different endpoint because the hash pins method/path/operationId)
    - Paths starting with /_admin are excluded from proxying since they'd conflict with the admin UI
    """
    extracted = _extract_operations(spec)
    result = SyncResult()

    seen_ids: set[str] = set()
    for item in extracted:
        if item.path.startswith(ADMIN_PATH_PREFIX):
            result.skipped_admin_conflict.append(item.label)
            continue

        seen_ids.add(item.operation_id)
        existing = session.get(Operation, item.operation_id)
        if existing is None:
            session.add(
                Operation(
                    operation_id=item.operation_id,
                    method=item.method,
                    path=item.path,
                    openapi_operation_id=item.openapi_operation_id,
                    summary=item.summary,
                    is_active=True,
                )
            )
            result.added.append(item.label)
        else:
            # method/path/openapi_operation_id cannot differ under the same hash,
            # so only summary and is_active can actually change here.
            changed = existing.summary != item.summary or not existing.is_active
            existing.summary = item.summary
            existing.is_active = True
            session.add(existing)
            if changed:
                result.updated.append(item.label)

    all_operations = session.exec(select(Operation)).all()
    for operation in all_operations:
        if operation.operation_id not in seen_ids and operation.is_active:
            operation.is_active = False
            session.add(operation)
            result.removed.append(f"{operation.method} {operation.path}")

    return result


def _get_latest_snapshot(session: Session) -> SchemaSnapshot | None:
    # sqlmodel field access is statically typed as `datetime`, not a Column, so pyright
    # cannot see that this is actually a SQLAlchemy InstrumentedAttribute at runtime.
    statement = select(SchemaSnapshot).order_by(desc(SchemaSnapshot.fetched_at)).limit(1)  # type: ignore[arg-type]
    return session.exec(statement).first()


@dataclass
class SchemaRefreshOutcome:
    snapshot: SchemaSnapshot
    # Result of this refresh run. Unlike snapshot.diff_summary (which may belong to an
    # older snapshot when the spec is unchanged), this always reflects the current run.
    result: SyncResult


async def refresh_backend_schema(session: Session, backend_config: BackendConfig) -> SchemaRefreshOutcome:
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
        if latest_snapshot is not None and latest_snapshot.spec_hash == spec_hash and not result.has_changes():
            # Spec is unchanged since the last snapshot: avoid piling up "no change" rows,
            # which would otherwise flood the history once periodic sync is introduced.
            session.commit()
            session.refresh(latest_snapshot)
            return SchemaRefreshOutcome(snapshot=latest_snapshot, result=result)

        snapshot = SchemaSnapshot(spec_hash=spec_hash, diff_summary=result.to_diff_summary())
        session.add(snapshot)

        session.commit()
        session.refresh(snapshot)
        return SchemaRefreshOutcome(snapshot=snapshot, result=result)
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


async def _maybe_run_scheduled_sync(engine: Engine, last_run_at: datetime | None) -> datetime | None:
    """Run a scheduled sync if the configured interval has elapsed since last_run_at.

    Returns the timestamp to use as last_run_at on the next tick (unchanged if no sync ran).
    Reading the interval and last_fetched_at fresh from the DB on every tick is what lets a
    change made from the GUI (or disabling auto sync entirely) take effect without a restart.
    """
    with Session(engine) as session:
        backend_config = session.get(BackendConfig, BACKEND_CONFIG_ID)
        if backend_config is None:
            return last_run_at

        interval = effective_sync_interval_seconds(backend_config)
        if interval <= 0:
            return last_run_at

        now = datetime.now(UTC)
        if last_run_at is not None and (now - last_run_at).total_seconds() < interval:
            return last_run_at

        try:
            await refresh_backend_schema(session, backend_config)
        except Exception:
            logger.warning("Scheduled schema sync failed for %s", backend_config.openapi_url, exc_info=True)
        return now


async def schema_sync_loop(engine: Engine, tick_seconds: float = SCHEDULER_TICK_SECONDS) -> None:
    """Periodically check whether a schema sync is due, until the task is cancelled.

    Intended to be started unconditionally as an asyncio task from the FastAPI lifespan and
    cancelled on shutdown; the configured interval (0 = disabled) is re-read from backend_config
    on every tick, so it can be changed from the GUI at any time.
    """
    last_run_at: datetime | None = None
    while True:
        await asyncio.sleep(tick_seconds)
        try:
            last_run_at = await _maybe_run_scheduled_sync(engine, last_run_at)
        except asyncio.CancelledError:
            raise
        except Exception:
            # Defensive: _maybe_run_scheduled_sync already handles sync failures internally, but
            # this ensures a truly unexpected error (e.g. a DB connectivity issue) never kills the loop.
            logger.exception("Unexpected error in schema sync loop")
