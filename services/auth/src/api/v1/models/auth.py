from pydantic import BaseModel
import uuid

class RequestLogin(BaseModel):
    username: str
    password: str

class ResponseLogin(BaseModel):
    access_token: str
    refresh_token: str
