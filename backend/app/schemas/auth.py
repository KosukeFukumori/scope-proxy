from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class UserRead(BaseModel):
    id: int
    username: str


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str


class UsernameChangeRequest(BaseModel):
    username: str
