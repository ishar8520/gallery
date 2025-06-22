from pydantic import BaseModel
import uuid

class AccessToken(BaseModel):
    access_token: str
    
class RefreshToken(BaseModel):
    refresh_token: str

class UserData(BaseModel):
    username: str
    email: str
    password: str 

class ReqRegistration(UserData):
    pass

class RespRegistration(AccessToken, RefreshToken):
    pass




