from pydantic import BaseModel


class OperationRead(BaseModel):
    operation_id: str
    method: str
    path: str
    openapi_operation_id: str | None
    summary: str | None
    is_active: bool
