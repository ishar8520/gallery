from pydantic import BaseModel
import uuid


class ResponseUser(BaseModel):
    user_id: uuid.UUID
    username: str
    email: str

class RequestPatchUser(BaseModel):
    username: str
    email: str
