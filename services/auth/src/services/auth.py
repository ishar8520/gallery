from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select, Select
from async_fastapi_jwt_auth import AuthJWT
from fastapi import Depends, Response
from hashlib import sha256
from datetime import timedelta
from typing import Tuple
import hmac

from src.dependences.postgres import get_async_pg, PostgresDep
from src.dependences.jwt import get_async_jwt, JWTDep
from src.api.v1.models.auth import (
    ReqRegistration,
    ReqLogin
)
from src.models.users import User
from src.services.exceptions import (
    EmailExistException,
    UsernameExistException,
    BadCredsException,
    UnauthorizedException
) 


class AuthService:
    pg_session: PostgresDep
    jwt_session: JWTDep

    def __init__(self, pg_session, jwt_session):
        self.pg_session = pg_session
        self.jwt_session = jwt_session

    async def get_register(self, request_model: ReqRegistration) -> Tuple[str, str]:
        username = await self.pg_session.get_one_or_none(select(User).where(User.username==request_model.username))
        if username:
            raise UsernameExistException
        email = await self.pg_session.get_one_or_none(select(User).where(User.email==request_model.email))
        if email:
            raise EmailExistException
        
        password = sha256(request_model.password.encode('utf-8')).hexdigest()
        user = User(username=request_model.username,
                    password=password,
                    email=request_model.email)
        await self.pg_session.add(user)
        return user.id

    async def get_login(self, request_model: ReqLogin):
        user = await self.pg_session.check_user(
            username=request_model.username,
            password=request_model.password
        )
        if not user:
            raise BadCredsException
        access_token = await self.jwt_session.create_access_token(user_id=user.id,
                                                 username=user.username,
                                                 email=user.email)
        return access_token

    async def get_logout(self):
        return await self.jwt_session.logout()

    async def get_user(self, token):
        await self.jwt_session.check_jwt(token)
        return await self.jwt_session.get_jwt_claim(token)      

        
    async def check(self):
        await self.jwt_session.check_jwt()
        return {'JWT': 'exist'}


def get_auth_service(
    pg_dep: AsyncSession = Depends(get_async_pg),
    jwt_dep: AuthJWT = Depends(get_async_jwt)) -> AuthService:
    return AuthService(pg_session=pg_dep, jwt_session=jwt_dep)
