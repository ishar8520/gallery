from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from async_fastapi_jwt_auth import AuthJWT
from async_fastapi_jwt_auth.auth_jwt import AuthJWTBearer
from fastapi import Depends
from datetime import timedelta
from typing import Annotated

from src.dependences.postgres import get_async_postgres, PostgresDep
from src.dependences.redis import get_async_redis, RedisDep
from src.models.users import User
from src.api.v1.models.auth import RequestLogin, ResponseLogin
from src.services.exceptions import (
    EmailExistException,
    UsernameExistException,
    BadCredsException,
    UnauthorizedException
) 

auth_jwt_dep = AuthJWTBearer()


class AuthService:
    pg_session: PostgresDep
    redis_session: RedisDep
    auth: AuthJWT

    def __init__(self, postgres, redis, auth):
        self.pg_session = postgres
        self.redis_session = redis
        self.auth = auth

    # async def get_register(self, request_model: RequestRegistration) -> Tuple[str, str]:
    #     username = await self.pg_session.get_one_or_none(select(User).where(User.username==request_model.username))
    #     if username:
    #         raise UsernameExistException
    #     email = await self.pg_session.get_one_or_none(select(User).where(User.email==request_model.email))
    #     if email:
    #         raise EmailExistException
        
    #     password = sha256(request_model.password.encode('utf-8')).hexdigest()
    #     user = User(username=request_model.username,
    #                 password=password,
    #                 email=request_model.email)
    #     await self.pg_session.add(user)
    #     return user.id

    async def get_login(self, request_model: RequestLogin):
        user = await self.pg_session.check_user(
            username=request_model.username,
            password=request_model.password
        )
        if not user:
            raise BadCredsException

        claim = {
            'email': user.email
        }
        access_token = await self.auth.create_access_token(
            subject=request_model.username, user_claims=claim)
        refresh_token = await self.auth.create_refresh_token(
            subject=request_model.username)
        expires = timedelta(hours=1)
        await self.redis_session.set_value(f'token:access:{user.id}', access_token, int(expires.total_seconds()))
        expires = timedelta(days=7)
        await self.redis_session.set_value(f'token:refresh:{user.id}', refresh_token, int(expires.total_seconds()))
        return ResponseLogin(
            access_token=access_token,
            refresh_token=refresh_token)

    async def get_logout(self):
        await self.auth.jwt_required()
        username = await self.auth.get_jwt_subject()
        user = await self.pg_session.get_one_or_none(select(User).where(User.username==username))
        await self.redis_session.drop_value(f'token:access:{user.id}')
        return await self.redis_session.drop_value(f'token:refresh:{user.id}')

    async def get_user(self):
        await self.auth.jwt_required()
        claim = await self.auth.get_raw_jwt()
        username = await self.auth.get_jwt_subject()
        return {
            'username': username,
            'email': claim['email']
        }
    

def get_auth_service(
    pg_dep: Annotated[AsyncSession, Depends(get_async_postgres)],
    redis_dep: Annotated[RedisDep, Depends(get_async_redis)],
    auth_dep: Annotated[AuthJWT, Depends(auth_jwt_dep)]
    ) -> AuthService:
    return AuthService(postgres=pg_dep, redis=redis_dep, auth=auth_dep)
