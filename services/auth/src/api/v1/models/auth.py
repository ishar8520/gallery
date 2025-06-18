from pydantic import BaseModel
import uuid


class ReqRegistration(BaseModel):
    username: str
    email: str
    password: str

class ResRegistration(BaseModel):
    id: uuid.UUID
