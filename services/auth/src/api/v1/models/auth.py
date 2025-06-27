from pydantic import BaseModel
from typing import List
import uuid


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
    roles: List[str]