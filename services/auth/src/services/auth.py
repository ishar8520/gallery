from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select, Select
from async_fastapi_jwt_auth import AuthJWT
from fastapi import Depends
from hashlib import sha256
from datetime import timedelta
import hmac

from src.dependences.postgres import get_async_session
from src.dependences.redis import get_async_redis, Redis
from src.dependences.jwt import get_async_jwt
from src.api.v1.models.auth import ReqRegistration
from src.models.users import User
from src.services.exceptions import (
    EmailExistException,
    UsernameExistException
) 


class AuthService:
    _pg_session: AsyncSession
    _redis_session: Redis
    _authorize: AuthJWT

    def __init__(self, pg_session, redis_session, authorize):
        self._pg_session = pg_session
        self._redis_session = redis_session
        self._authorize = authorize

    async def get_register(self, request_model: ReqRegistration) -> User:
        try:
            username = await self.get_one_or_none(select(User).where(User.username==request_model.username))
            if username:
                raise UsernameExistException
            email = await self.get_one_or_none(select(User).where(User.email==request_model.email))
            if email:
                raise EmailExistException
            
            password = sha256(request_model.password.encode('utf-8')).hexdigest()
            user = User(username=request_model.username,
                        password=password,
                        email=request_model.email)
            self._pg_session.add(user)
            await self._pg_session.commit()
            await self._pg_session.refresh(user)
            access_token, refresh_token = await self.get_token(user)
        except SQLAlchemyError:
            await self._pg_session.rollback()
        return access_token, refresh_token

    # async def test(self):
    #     token = await self._authorize.create_access_token(subject='sss')
    #     expires = timedelta(minutes=1)
    #     await self._redis_session.set(f'token:access:123',
    #                                     token,
    #                                     ex=int(expires.total_seconds()))
    #     return {'token': token}

    async def get_one_or_none(self, statement: Select):
        result = await self._pg_session.execute(statement)
        return result.scalar_one_or_none()
    
    async def get_token(self, user: User):
        token_data = {
            'username': user.username,
            'email': user.email
        }
        access_token = await self._authorize.create_access_token(subject=user.username, user_claims=token_data)
        refresh_token = await self._authorize.create_refresh_token(subject=user.username)
        expires_access = timedelta(hours=1)
        expires_refresh = timedelta(days=1)
        await self._redis_session.set(f'token:access:{user.id}',
                                        access_token,
                                        ex=int(expires_access.total_seconds()))
        await self._redis_session.set(f'token:refresh:{user.id}',
                                        refresh_token,
                                        ex=int(expires_refresh.total_seconds()))
        return access_token, refresh_token

    async def read_token(self, token: str):
        pass

def get_auth_service(
    pg_session: AsyncSession = Depends(get_async_session),
    redis_session: Redis = Depends(get_async_redis),
    authorize: AuthJWT = Depends(get_async_jwt)) -> AuthService:
    return AuthService(pg_session=pg_session, redis_session=redis_session, authorize=authorize)
