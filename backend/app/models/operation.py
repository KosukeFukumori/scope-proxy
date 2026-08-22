from sqlmodel import Field, SQLModel


class Operation(SQLModel, table=True):
    """Endpoint definition keyed by a hash of (method, path, OpenAPI operationId).

    Permissions are keyed on this hash rather than the raw operationId or the
    path string, so a permission stays valid only while all three components
    stay identical. If a schema change reuses an operationId or a path/method
    for a different endpoint, the hash changes and permissions are not
    inherited (fail-safe).
    """

    # sqlmodel declares __tablename__ as declared_attr; pyright cannot narrow a plain str assignment.
    __tablename__ = "operations"  # type: ignore[assignment]

    operation_id: str = Field(primary_key=True)
    method: str
    path: str
    # operationId as declared in the upstream OpenAPI spec (None if absent).
    # Kept for display purposes; the identity used for permissions is operation_id.
    openapi_operation_id: str | None = None
    summary: str | None = None
    is_active: bool = Field(default=True)
