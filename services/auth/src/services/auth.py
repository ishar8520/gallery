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
from src.services import exceptions 


auth_jwt_dep = AuthJWTBearer()


@AuthJWT.load_config
def get_config():
    return settings.jwt


class AuthService:
    pg_session: PostgresDep
    redis_session: RedisDep
    jwt: AuthJWT

    def __init__(self, postgres: AsyncSession, redis: RedisDep, jwt: AuthJWT) -> None:
        self.pg_session = postgres
        self.redis_session = redis
        self.jwt = jwt

    async def get_login(self, request_model: RequestLogin) -> ResponseLogin:
        user = await self.pg_session.get_user_by_username(request_model.username)
        if not user or not user.password == sha256(request_model.password.encode('utf-8')).hexdigest():
            raise exceptions.BadCredsException
        roles = await self.pg_session.get_user_roles(user.id)
        claim = {'email': user.email,
                'user_id': str(user.id),
                'roles': roles}
        access_token, refresh_token = await self.get_tokens(user.username, user.id, claim)
        return ResponseLogin(
            access_token=access_token,
            refresh_token=refresh_token)

    async def get_logout(self) -> None:
        claim = await self.jwt.get_raw_jwt()
        await self.redis_session.drop_value(f'token:access:{claim["user_id"]}')
        await self.redis_session.drop_value(f'token:refresh:{claim["user_id"]}')
        return await self.jwt.unset_jwt_cookies()

    async def get_me(self) -> ResponseMe:
        claim = await self.jwt.get_raw_jwt()
        user_id = await self.jwt.get_jwt_subject()
        return ResponseMe(
            user_id=user_id,
            username=claim['username'],
            email=claim['email'],
            roles=claim['roles'])         

    async def get_update_token(self, user_id: UUID) -> ResponseLogin:
        user = await self.pg_session.get_user_by_id(user_id)
        roles = await self.pg_session.get_user_roles(user_id)
        claim = {'username': user.username,
                 'email': user.email,
                 'user_id': str(user_id),
                 'roles': roles}
        access_token, refresh_token = await self.get_tokens(user.id, claim)
        return ResponseLogin(
            access_token=access_token,
            refresh_token=refresh_token)
        
    async def get_refresh(self, refresh_token: str):
        claim = await self.jwt.get_raw_jwt()
        user_id = await self.jwt.get_jwt_subject()

    async def get_tokens(self, user_id: UUID, claim: dict):
        access_token = await self.jwt.create_access_token(
            subject=user_id, user_claims=claim)
        refresh_token = await self.jwt.create_refresh_token(
            subject=user_id, user_claims=claim)
        await self.jwt.set_access_cookies(access_token)
        await self.jwt.set_refresh_cookies(refresh_token)
        expires = timedelta(hours=1)
        await self.redis_session.set_value(f'token:access:{user_id}',
                                           access_token,
                                           int(expires.total_seconds()))
        expires = timedelta(days=7)
        await self.redis_session.set_value(f'token:refresh:{user_id}',
                                           refresh_token,
                                           int(expires.total_seconds()))
        return access_token, refresh_token

    async def check_role(self, role: str):
        user = await self.get_me()
        if not role in user.roles:
            raise exceptions.BadPermissionsException
        return True

def get_auth_service(
    pg_dep: Annotated[AsyncSession, Depends(get_async_postgres)],
    redis_dep: Annotated[RedisDep, Depends(get_async_redis)],
    auth_dep: Annotated[AuthJWT, Depends(auth_jwt_dep)]
    ) -> AuthService:
    return AuthService(postgres=pg_dep, redis=redis_dep, jwt=auth_dep)
