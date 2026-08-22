import hashlib
import json
import re

from openapi_core import OpenAPI
from openapi_core.templating.paths.exceptions import (
    OperationNotFound,
    PathNotFound,
    ServerNotFound,
)
from openapi_core.templating.paths.finders import APICallPathFinder

from app.models.operation import Operation

_PATH_PARAM_RE = re.compile(r"\{(\w+)\}")


def _build_minimal_spec(operations: list[Operation]) -> dict:
    """Build a minimal OpenAPI spec from active Operations, used only for path matching via openapi-core."""
    paths: dict[str, dict] = {}
    for op in operations:
        path_item = paths.setdefault(op.path, {})
        param_names = _PATH_PARAM_RE.findall(op.path)
        if param_names:
            path_item["parameters"] = [
                {
                    "name": name,
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string"},
                }
                for name in param_names
            ]
        path_item[op.method.lower()] = {
            "operationId": op.operation_id,
            "responses": {"default": {"description": ""}},
        }

    return {
        "openapi": "3.0.0",
        "info": {"title": "scope-proxy backend", "version": "1"},
        "paths": paths,
    }


class OperationMatcher:
    def __init__(self, operations: list[Operation]) -> None:
        spec = _build_minimal_spec(operations)
        api = OpenAPI.from_dict(spec)
        self._finder = APICallPathFinder(api.spec, base_url="")

    def match(self, method: str, path: str) -> str | None:
        try:
            result = self._finder.find(method.lower(), path)
        except (PathNotFound, OperationNotFound, ServerNotFound):
            return None
        return str(result.operation["operationId"])


def operations_cache_key(operations: list[Operation]) -> str:
    fingerprint = sorted((op.operation_id, op.method, op.path) for op in operations)
    return hashlib.sha256(json.dumps(fingerprint).encode()).hexdigest()


def build_operation_matcher(operations: list[Operation]) -> OperationMatcher:
    return OperationMatcher(operations)


class _CachedOperationMatcher:
    """Process-local single-slot cache for the last built OperationMatcher.

    Building an OperationMatcher parses and validates a full OpenAPI spec via
    openapi-core, which is expensive. Operations rarely change (only on schema
    sync), so we keep a single cached matcher keyed by operations_cache_key()
    and only rebuild it when the fingerprint changes.
    """

    def __init__(self) -> None:
        self._key: str | None = None
        self._matcher: OperationMatcher | None = None

    def get(self, operations: list[Operation]) -> OperationMatcher:
        key = operations_cache_key(operations)
        if key != self._key or self._matcher is None:
            self._matcher = build_operation_matcher(operations)
            self._key = key
        return self._matcher

    def clear(self) -> None:
        """Reset the cache. Exposed for tests that need to isolate cache state."""
        self._key = None
        self._matcher = None


_cache = _CachedOperationMatcher()


def get_cached_operation_matcher(operations: list[Operation]) -> OperationMatcher:
    """Return a cached OperationMatcher for the given operations, rebuilding only if
    the operations fingerprint (operations_cache_key) has changed since the last call.
    """
    return _cache.get(operations)


def reset_operation_matcher_cache() -> None:
    """Clear the cached OperationMatcher. Intended for test isolation."""
    _cache.clear()
