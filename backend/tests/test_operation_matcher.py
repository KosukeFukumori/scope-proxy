from app.models.operation import Operation
from app.services.operation_matcher import (
    build_operation_matcher,
    get_cached_operation_matcher,
    operations_cache_key,
    reset_operation_matcher_cache,
)

OPERATIONS = [
    Operation(operation_id="listUsers", method="GET", path="/users", is_active=True),
    Operation(operation_id="getUser", method="GET", path="/users/{id}", is_active=True),
    Operation(operation_id="createUser", method="POST", path="/users", is_active=True),
    Operation(operation_id="oldGetUser", method="GET", path="/legacy/{id}", is_active=False),
]


def test_match_exact_path() -> None:
    matcher = build_operation_matcher(OPERATIONS)
    assert matcher.match("GET", "/users") == "listUsers"


def test_match_different_method_same_path() -> None:
    matcher = build_operation_matcher(OPERATIONS)
    assert matcher.match("POST", "/users") == "createUser"


def test_match_path_with_parameter() -> None:
    matcher = build_operation_matcher(OPERATIONS)
    assert matcher.match("GET", "/users/123") == "getUser"
    assert matcher.match("get", "/users/abc-def") == "getUser"


def test_no_match_for_unknown_path() -> None:
    matcher = build_operation_matcher(OPERATIONS)
    assert matcher.match("GET", "/unknown") is None


def test_no_match_for_unknown_method_on_known_path() -> None:
    matcher = build_operation_matcher(OPERATIONS)
    assert matcher.match("DELETE", "/users") is None


def test_matches_inactive_operation_too() -> None:
    """The is_active check is the caller's responsibility; the matcher only matches path/method."""
    matcher = build_operation_matcher(OPERATIONS)
    assert matcher.match("GET", "/legacy/1") == "oldGetUser"


def test_empty_operations() -> None:
    matcher = build_operation_matcher([])
    assert matcher.match("GET", "/anything") is None


def test_cached_matcher_reuses_instance_for_same_fingerprint() -> None:
    reset_operation_matcher_cache()
    matcher_1 = get_cached_operation_matcher(OPERATIONS)
    matcher_2 = get_cached_operation_matcher(list(OPERATIONS))  # different list, same content
    assert matcher_1 is matcher_2


def test_cached_matcher_rebuilds_when_operations_change() -> None:
    reset_operation_matcher_cache()
    matcher_1 = get_cached_operation_matcher(OPERATIONS)

    changed_operations = [
        *OPERATIONS,
        Operation(operation_id="deleteUser", method="DELETE", path="/users/{id}", is_active=True),
    ]
    matcher_2 = get_cached_operation_matcher(changed_operations)

    assert matcher_1 is not matcher_2
    # The stale matcher must not still be served for the new fingerprint.
    assert matcher_2.match("DELETE", "/users/1") == "deleteUser"
    assert matcher_1.match("DELETE", "/users/1") is None


def test_operations_cache_key_is_order_independent() -> None:
    assert operations_cache_key(OPERATIONS) == operations_cache_key(list(reversed(OPERATIONS)))


def test_operations_cache_key_changes_with_content() -> None:
    other = [*OPERATIONS, Operation(operation_id="extra", method="GET", path="/extra", is_active=True)]
    assert operations_cache_key(OPERATIONS) != operations_cache_key(other)
