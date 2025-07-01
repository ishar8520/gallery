from pydantic import BaseModel
import uuid


class RequestRegistration(BaseModel):
    username: str
    email: str
    password: str


class ResponseRegistration(BaseModel):
    id: uuid.UUID
