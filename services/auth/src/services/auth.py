from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import Depends, HTTPException


from src.dependences.postgres import get_async_session
from src.api.v1.models.auth import ReqRegistration
from src.models.users import Users

class AuthService:
    _pg_session: AsyncSession

    def __init__(self, session):
        self._pg_session = session

    async def get_register(self, request_model: ReqRegistration):
        statement = select(Users).where(Users.username==request_model.username)
        username = await self._pg_session(statement)
        pass


def get_auth_service(session: AsyncSession = Depends(get_async_session)) -> AuthService:
    return AuthService(session=session)
