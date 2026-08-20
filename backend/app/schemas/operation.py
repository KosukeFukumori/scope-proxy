from pydantic import BaseModel


class OperationRead(BaseModel):
    operation_id: str
    method: str
    path: str
    summary: str | None
    is_active: bool
