from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select, Select
from fastapi import Depends
from hashlib import sha256

from src.dependences.postgres import get_async_session
from src.api.v1.models.auth import ReqRegistration
from src.models.users import User
from src.services.exceptions import (
    EmailExistException,
    UsernameExistException
) 


class AuthService:
    _pg_session: AsyncSession

    def __init__(self, session):
        self._pg_session = session

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
        except SQLAlchemyError:
            await self._pg_session.rollback()
        return user

    async def get_one_or_none(self, statement: Select):
        result = await self._pg_session.execute(statement)
        return result.scalar_one_or_none()

def get_auth_service(session: AsyncSession = Depends(get_async_session)) -> AuthService:
    return AuthService(session=session)
