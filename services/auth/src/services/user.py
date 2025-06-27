from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from hashlib import sha256

from src.dependences.postgres import get_async_postgres, PostgresDep
from src.dependences.redis import get_async_redis, RedisDep
from src.services.exceptions import UsernameExistException, EmailExistException
from src.models.user import User, UserRoles
from src.models.enums import Roles
from src.api.v1.models.registration import RequestRegistration
from src.api.v1.models.user import ResponseUser


class UserService:
    pg_session: PostgresDep
    redis_session: RedisDep

    def __init__(self, postgres, redis):
        self.pg_session = postgres
        self.redis_session = redis

    async def get_register(self, request_model: RequestRegistration) -> UUID:
        username = await self.pg_session.get_user_by_username(request_model.username)
        if username:
            raise UsernameExistException
        email = await self.pg_session.get_user_by_email(request_model.email)
        if email:
            raise EmailExistException
        
        password = sha256(request_model.password.encode('utf-8')).hexdigest()
        
        role = await self.pg_session.get_role(Roles.USER)
        user = User(username=request_model.username,
                    password=password,
                    email=request_model.email)
        user_role = UserRoles(user=user, role=role)
        await self.pg_session.add_user(user, user_role)
        return user.id
    
    async def get_user(self, user_id: str):
        user = await self.pg_session.get_user_by_id(user_id)
        return ResponseUser(
            user_id=user.id,
            username=user.username,
            email=user.email,
            roles=user.roles
        )
        
    async def get_delete_user(self, user_id: str):
        return await self.pg_session.delete_user(user_id)
    
def get_user_service(
    pg_dep: Annotated[AsyncSession, Depends(get_async_postgres)],
    redis_dep: Annotated[RedisDep, Depends(get_async_redis)],
    ) -> UserService:
    return UserService(postgres=pg_dep, redis=redis_dep)
