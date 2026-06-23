import uuid

from pydantic import BaseModel


class ResponseUser(BaseModel):
    user_id: uuid.UUID
    username: str
    email: str

class RequestPatchUser(BaseModel):
    username: str
    email: str
