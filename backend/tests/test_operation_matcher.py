from app.models.operation import Operation
from app.services.operation_matcher import build_operation_matcher

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
