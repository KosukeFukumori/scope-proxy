from sqlmodel import Field, SQLModel


class Operation(SQLModel, table=True):
    """Endpoint definition keyed by OpenAPI operationId.

    Permissions are keyed on operation_id rather than the path string, to avoid
    incorrectly inheriting permissions if a schema change reuses a path/method
    for a different endpoint.
    """

    __tablename__ = "operations"

    operation_id: str = Field(primary_key=True)
    method: str
    path: str
    summary: str | None = None
    is_active: bool = Field(default=True)
