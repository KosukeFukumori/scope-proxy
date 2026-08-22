import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime

import httpx
from sqlalchemy import desc
from sqlmodel import Session, select

from app.models.backend_config import BackendConfig
from app.models.operation import Operation
from app.models.schema_snapshot import SchemaSnapshot

ADMIN_PATH_PREFIX = "/_admin"

# Length (in hex chars) of the truncated sha256 digest used as operation_id.
# 32 hex chars = 128 bits, plenty to avoid collisions.
OPERATION_ID_LENGTH = 32


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
    spec = await fetch_openapi_spec(backend_config.openapi_url)
    spec_hash = hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest()

    result = sync_operations(session, spec)

    backend_config.last_fetched_at = datetime.now(UTC)
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
