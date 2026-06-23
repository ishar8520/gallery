
from pydantic import BaseModel


class RequestRegistration(BaseModel):
    username: str
    email: str
    password: str
