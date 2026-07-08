import uuid

from pydantic import BaseModel


class ResponseUser(BaseModel):
    user_id: uuid.UUID
    username: str
    email: str


class ResponseUserAdmin(BaseModel):
    user_id: uuid.UUID
    username: str
    email: str
    roles: list[str]


class RequestPatchUser(BaseModel):
    username: str
    email: str


class RequestChangePassword(BaseModel):
    current_password: str
    new_password: str
