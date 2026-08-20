import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime

import httpx
from sqlmodel import Session, select

from app.models.backend_config import BackendConfig
from app.models.operation import Operation
from app.models.schema_snapshot import SchemaSnapshot

ADMIN_PATH_PREFIX = "/_admin"


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
    """取得済みのOpenAPI specとoperationsテーブルの差分を反映する。

    - 新規operationId -> is_active=Trueで追加。権限は自動付与しない
    - 継続 -> method/path/summaryを更新、is_active=Trueに戻す
    - 消滅 -> is_active=Falseに変更(token_permissionsは削除しない)
    - /_adminで始まるpathは管理画面と衝突するためプロキシ対象から除外する
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


async def refresh_backend_schema(session: Session, backend_config: BackendConfig) -> SchemaSnapshot:
    spec = await fetch_openapi_spec(backend_config.openapi_url)
    spec_hash = hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest()

    result = sync_operations(session, spec)

    backend_config.last_fetched_at = datetime.now(UTC)
    session.add(backend_config)

    snapshot = SchemaSnapshot(spec_hash=spec_hash, diff_summary=result.to_diff_summary())
    session.add(snapshot)

    session.commit()
    session.refresh(snapshot)
    return snapshot
