from sqlalchemy.ext.asyncio import AsyncSession
from async_fastapi_jwt_auth import AuthJWT
from async_fastapi_jwt_auth.auth_jwt import AuthJWTBearer
from fastapi import Depends
from datetime import timedelta
from typing import Annotated
from hashlib import sha256
from uuid import UUID

from src.core.config import settings
from src.dependences.postgres import get_async_postgres, PostgresDep
from src.dependences.redis import get_async_redis, RedisDep
from src.api.v1.models.auth import (
    RequestLogin,
    ResponseLogin,
    ResponseMe
)
from src.services.exceptions import (
    BadCredsException,
) 


auth_jwt_dep = AuthJWTBearer()


@AuthJWT.load_config
def get_config():
    return settings.jwt


class AuthService:
    pg_session: PostgresDep
    redis_session: RedisDep
    auth: AuthJWT

    def __init__(self, postgres: AsyncSession, redis: RedisDep, auth: AuthJWT) -> None:
        self.pg_session = postgres
        self.redis_session = redis
        self.auth = auth

    async def get_login(self, request_model: RequestLogin) -> ResponseLogin:
        user = await self.pg_session.get_user_by_username(request_model.username)
        if not user or not user.password == sha256(request_model.password.encode('utf-8')).hexdigest():
            raise BadCredsException
        roles = await self.pg_session.get_user_roles(user.id)
        claim = {'email': user.email,
                'user_id': str(user.id),
                'roles': roles}
        access_token = await self.auth.create_access_token(
            subject=request_model.username, user_claims=claim)
        refresh_token = await self.auth.create_refresh_token(
            subject=request_model.username)
        await self.auth.set_access_cookies(access_token)
        await self.auth.set_refresh_cookies(refresh_token)
        expires = timedelta(hours=1)
        await self.redis_session.set_value(f'token:access:{user.id}', access_token, int(expires.total_seconds()))
        expires = timedelta(days=7)
        await self.redis_session.set_value(f'token:refresh:{user.id}', refresh_token, int(expires.total_seconds()))
        return ResponseLogin(
            access_token=access_token,
            refresh_token=refresh_token)

    async def get_logout(self) -> None:
        claim = await self.auth.get_raw_jwt()
        await self.redis_session.drop_value(f'token:access:{claim["user_id"]}')
        await self.redis_session.drop_value(f'token:refresh:{claim["user_id"]}')
        return await self.auth.unset_jwt_cookies()

    async def get_me(self) -> ResponseMe:
        claim = await self.auth.get_raw_jwt()
        username = await self.auth.get_jwt_subject()
        return ResponseMe(
            user_id=claim['user_id'],
            username=username,
            email=claim['email'],
            roles=claim['roles'])         

    async def get_refresh(self, user_id: UUID) -> ResponseLogin:
        user = await self.pg_session.get_user_by_id(user_id)
        roles = await self.pg_session.get_user_roles(user_id)
        claim = {'email': user.email,
                'user_id': str(user_id),
                'roles': roles}
        access_token = await self.auth.create_access_token(
            subject=user.username, user_claims=claim)
        refresh_token = await self.auth.create_refresh_token(
            subject=user.username)
        await self.auth.set_access_cookies(access_token)
        await self.auth.set_refresh_cookies(refresh_token)
        expires = timedelta(hours=1)
        await self.redis_session.set_value(f'token:access:{user.id}', access_token, int(expires.total_seconds()))
        expires = timedelta(days=7)
        await self.redis_session.set_value(f'token:refresh:{user.id}', refresh_token, int(expires.total_seconds()))
        return ResponseLogin(
            access_token=access_token,
            refresh_token=refresh_token)

def get_auth_service(
    pg_dep: Annotated[AsyncSession, Depends(get_async_postgres)],
    redis_dep: Annotated[RedisDep, Depends(get_async_redis)],
    auth_dep: Annotated[AuthJWT, Depends(auth_jwt_dep)]
    ) -> AuthService:
    return AuthService(postgres=pg_dep, redis=redis_dep, auth=auth_dep)
