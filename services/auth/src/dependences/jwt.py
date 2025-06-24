from async_fastapi_jwt_auth import AuthJWT
from fastapi import Depends, Request, Response
from datetime import timedelta
from typing import Annotated

from src.core.config import settings
from src.dependences.redis import get_async_redis, RedisDep
from src.services.exceptions import UnauthorizedException


@AuthJWT.load_config
def get_config():
    return settings

class JWTDep:
    auth_jwt: AuthJWT
    redis_session: RedisDep
    
    
    def __init__(self, request: Request, response: Response, redis_session: RedisDep):
        self.auth_jwt = AuthJWT()
        self.redis_session = redis_session
        self.response = response
        self.request = request
    
    async def create_access_token(self, user_id: str, username: str, email: str):
        token_data = {
            'email': email
        }
        access_token = await self.auth_jwt.create_access_token(subject=username, user_claims=token_data)
        expires = timedelta(hours=1)
        await self.redis_session.set_value(key=f'token:access:{user_id}',
                                     value=access_token,
                                     expires=int(expires.total_seconds()))
        return access_token
        
    async def logout(self, token):
        try:
            await self.check_jwt(token)
            return {'logout': 'success'}
        except Exception as errr:
            import traceback
            traceback.print_exc()
            print(errr)
        
    async def get_jwt_claim(self, token):
        await self.check_jwt(token)
        current_user = await self.auth_jwt.get_jwt_subject()
        claims = await self.auth_jwt.get_raw_jwt()
        return {
            'username': current_user,
            'email': claims['email']
        }
        
    async def check_jwt(self, token):
        try:
            await self.auth_jwt.jwt_required(token)
        except Exception:
            raise UnauthorizedException
        

async def get_async_jwt(
        request: Request,
        response: Response,
        redis_session: Annotated[RedisDep, Depends(get_async_redis)]
    ):
    return JWTDep(request, response, redis_session)
