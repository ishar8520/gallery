from pydantic import BaseModel
import uuid

class AccessToken(BaseModel):
    access_token: str
    
class RefreshToken(BaseModel):
    refresh_token: str

class UserIDModel(BaseModel):
    id: uuid.UUID

class UsernameModel(BaseModel):
    username: str
    
class EmailModel(BaseModel):
    email: str
    
class PasswordModel(BaseModel):
    password: str 

class ReqRegistration(PasswordModel, EmailModel, UsernameModel):
    pass

class RespRegistration(UserIDModel):
    pass

class ReqLogin(PasswordModel, UsernameModel):
    pass

class RespLogin(AccessToken):
    pass

