from pydantic import BaseModel
from typing import List

class RequestLogin(BaseModel):
    username: str
    password: str

class ResponseLogin(BaseModel):
    access_token: str
    refresh_token: str

class ResponseMe(BaseModel):
    user_id: str
    username: str
    email: str
    roles: List[str]