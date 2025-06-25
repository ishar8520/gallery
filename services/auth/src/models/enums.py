from pydantic import BaseModel
from enum import Enum

class Roles(str, Enum):
    USER = 'user'
    ADMIN = 'admin'
