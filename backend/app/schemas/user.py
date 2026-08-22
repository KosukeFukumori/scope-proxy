from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserSummary(BaseModel):
    id: int
    email: str
    created_at: datetime
