import uuid

from pydantic import BaseModel


class RequestLogin(BaseModel):
    username: str
    password: str


class ResponseLogin(BaseModel):
    access_token: str
    refresh_token: str


class ResponseMe(BaseModel):
    user_id: uuid.UUID
    username: str
    email: str
    roles: list[str]
