from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from hashlib import sha256

from src.dependences.postgres import get_async_postgres, PostgresDep
from src.services import exceptions
from src.models.user import User, UserRoles
from src.models.enums import Roles
from src.api.v1.models.registration import RequestRegistration
from src.api.v1.models.user import ResponseUser, RequestPatchUser


class UserService:
    pg_session: PostgresDep

    def __init__(self, postgres: AsyncSession) -> None:
        self.pg_session = postgres

    async def get_register(self, request_model: RequestRegistration) -> UUID:
        try:
            user = await self.pg_session.get_user_by_username(request_model.username)
            if user:
                raise exceptions.UsernameExistException
            email = await self.pg_session.get_user_by_email(request_model.email)
            if email:
                raise exceptions.EmailExistException
        except (exceptions.UsernameExistException, exceptions.EmailExistException):
            raise exceptions.UserExistException
        role = await self.pg_session.get_role(Roles.USER)
        password = sha256(request_model.password.encode('utf-8')).hexdigest()
        user = User(username=request_model.username,
                    password=password,
                    email=request_model.email)
        user_role = UserRoles(user=user, role=role)
        user_id = await self.pg_session.add_user(user)
        await self.pg_session.add_user_role(user_role)
        return user_id
        
    async def get_user(self, user_id: UUID) -> ResponseUser:
        user = await self.pg_session.get_user_by_id(user_id)
        if not user:
            raise exceptions.UserNotFoundException
        return ResponseUser(
            user_id=user.id,
            username=user.username,
            email=user.email)

    async def delete_user(self, user_id: UUID) -> None:
        user = await self.pg_session.get_user_by_id(user_id)
        if not user:
            raise exceptions.UserNotFoundException
        return await self.pg_session.delete_user(user_id)
    
    async def patch_user(self, user_id: UUID, user_update: RequestPatchUser) -> UUID:
        user = await self.pg_session.get_user_by_id(user_id)
        if not user:
            raise exceptions.UserNotFoundException
        await self.check_exist_user(current_user=user, update_user=user_update)
        if user_update.username not in [user.username, None]:
            user.username = user_update.username
        if user_update.email not in [user.email, None]:
            user.email = user_update.email
        return await self.pg_session.add_user(user)

    async def check_exist_user(self, current_user: User, update_user: RequestPatchUser) -> bool:
        for field, value in update_user:
            if field == 'username' and value != current_user.username:
                user = await self.pg_session.get_user_by_username(value)
                if user:
                    raise exceptions.UsernameExistException
            elif field == 'email' and value != current_user.email:
                email = await self.pg_session.get_user_by_email(value)
                if email:
                    raise exceptions.EmailExistException
        return True
        

def get_user_service(
    pg_dep: Annotated[AsyncSession, Depends(get_async_postgres)],
    ) -> UserService:
    return UserService(postgres=pg_dep)
