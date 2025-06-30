from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from hashlib import sha256

from src.dependences.postgres import get_async_postgres, PostgresDep
from src.dependences.redis import get_async_redis, RedisDep
from src.services.exceptions import UsernameExistException, EmailExistException, UserNotFoundException, UserExistException
from src.models.user import User, UserRoles
from src.models.enums import Roles
from src.api.v1.models.registration import RequestRegistration
from src.api.v1.models.user import ResponseUser, RequestPatchUser


class UserService:
    pg_session: PostgresDep
    redis_session: RedisDep

    def __init__(self, postgres, redis):
        self.pg_session = postgres
        self.redis_session = redis

    async def get_register(self, request_model: RequestRegistration) -> UUID:
        if not await self.check_exist_user(username=request_model.username, 
                                           email=request_model.email):
            raise UserExistException
        role = await self.pg_session.get_role(Roles.USER)
        password = sha256(request_model.password.encode('utf-8')).hexdigest()
        user = User(username=request_model.username,
                    password=password,
                    email=request_model.email)
        user_role = UserRoles(user=user, role=role)
        user = await self.pg_session.add_user(user)
        await self.pg_session.add_role(user_role)
        return user.id
    
    async def get_user(self, user_id: UUID):
        user = await self.pg_session.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundException
        return ResponseUser(
            user_id=user.id,
            username=user.username,
            email=user.email)

    async def delete_user(self, user_id: UUID):
        user = await self.pg_session.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundException
        return await self.pg_session.delete_user(user_id)
    
    async def patch_user(self, user_id: UUID, user_update: RequestPatchUser):
        user = await self.pg_session.get_user_by_id(user_id=user_id)
        if not user:
            raise UserNotFoundException
        if not await self.check_exist_user(username=user_update.username, 
                                           email=user_update.email):
            raise UserExistException
        if user_update.username not in [user.username, None]:
            user.username = user_update.username
        if user_update.email not in [user.email, None]:
            user.email = user_update.email
        return await self.pg_session.add_user(user)

    async def check_exist_user(self, username: str, email: str):
        user = await self.pg_session.get_user_by_username(username)
        if user:
            return False
        email = await self.pg_session.get_user_by_email(email)
        if email:
            return False
        return True
        


def get_user_service(
    pg_dep: Annotated[AsyncSession, Depends(get_async_postgres)],
    redis_dep: Annotated[RedisDep, Depends(get_async_redis)],
    ) -> UserService:
    return UserService(postgres=pg_dep, redis=redis_dep)
