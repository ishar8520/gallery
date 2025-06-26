from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from uuid import UUID
from hashlib import sha256

from src.dependences.postgres import get_async_postgres, PostgresDep
from src.dependences.redis import get_async_redis, RedisDep
from src.services.exceptions import UsernameExistException, EmailExistException
from src.models.users import User
from src.api.v1.models.registration import RequestRegistration

class UserService:
    pg_session: PostgresDep
    redis_session: RedisDep

    def __init__(self, postgres, redis):
        self.pg_session = postgres
        self.redis_session = redis

    async def get_register(self, request_model: RequestRegistration) -> UUID:
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
        await self.pg_session.add_user(user)
        return user.id
    
    async def get_delete_user(self, user_id: str):
        print('USER', user_id)
        # await self.pg_session.check_user()
        await self.pg_session.delete_user(user_id)
        return {'as': user_id}
    
def get_user_service(
    pg_dep: Annotated[AsyncSession, Depends(get_async_postgres)],
    redis_dep: Annotated[RedisDep, Depends(get_async_redis)],
    ) -> UserService:
    return UserService(postgres=pg_dep, redis=redis_dep)
