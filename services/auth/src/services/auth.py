from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select, Select
from fastapi import Depends, HTTPException
from http import HTTPStatus

from src.dependences.postgres import get_async_session
from src.api.v1.models.auth import ReqRegistration
from src.models.users import User


class AuthException(Exception):
    pass

class AuthService:
    _pg_session: AsyncSession

    def __init__(self, session):
        self._pg_session = session

    async def get_register(self, request_model: ReqRegistration) -> User:
        try:
            username = await self.get_one_or_none(select(User).where(User.username==request_model.username))
            if username:
                raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail='User with this username already exists')
            email = await self.get_one_or_none(select(User).where(User.email==request_model.email))
            if email:
                raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail='User with this email already exists')
            
            user = User(username=request_model.username,
                        password=request_model.password,
                        email=request_model.email)
            self._pg_session.add(user)
            await self._pg_session.commit()
            await self._pg_session.refresh(user)
        except SQLAlchemyError as error:
            print(error)
            await self._pg_session.rollback()
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail='SQL Exception')
        return user

    async def get_one_or_none(self, statement: Select):
        result = await self._pg_session.execute(statement)
        return result.scalar_one_or_none()

def get_auth_service(session: AsyncSession = Depends(get_async_session)) -> AuthService:
    return AuthService(session=session)
