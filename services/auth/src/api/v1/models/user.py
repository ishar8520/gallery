from pydantic import BaseModel
import uuid
from typing import List


class ResponseUser(BaseModel):
    user_id: uuid.UUID
    username: str
    email: str

class RequestPatchUser(BaseModel):
    username: set
    email: str
