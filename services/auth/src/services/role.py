from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from src.services import exceptions
from src.dependences.postgres import PostgresDep, get_async_postgres
from src.models.enums import Roles
from src.models.user import UserRoles

class RoleService:
    pg_session: PostgresDep

    def __init__(self, postgres):
        self.pg_session=postgres


    async def add_user_role(self, user_id: uuid.UUID, role: Roles):
        user = await self.pg_session.get_user_by_id(user_id)
        if not user:
            raise exceptions.UserNotFoundException
        user_roles = await self.pg_session.get_user_roles(user_id)
        if role in user_roles:
            raise exceptions.RoleExistException
        role = await self.pg_session.get_role(role)
        user_role = UserRoles(user=user, role=role)
        user_id = await self.pg_session.add_user(user)
        return await self.pg_session.add_user_role(user_role)

    async def get_user_role(self, user_id: uuid.UUID):
        user = await self.pg_session.get_user_by_id(user_id)
        if not user:
            raise exceptions.UserNotFoundException
        user_roles = await self.pg_session.get_user_roles(user_id)
        return user_roles

    async def delete_user_role(self, user_id: uuid.UUID, role: Roles):
        user = await self.pg_session.get_user_by_id(user_id)
        if not user:
            raise exceptions.UserNotFoundException
        user_roles = await self.pg_session.get_user_roles(user_id)
        if role not in user_roles:
            raise exceptions.RoleNotFoundException
        role = await self.pg_session.get_role(role)
        return await self.pg_session.delete_user_role(user, role)
        

async def get_role_service(
    pg_dep: Annotated[AsyncSession, Depends(get_async_postgres)],
    ) -> RoleService:
    return RoleService(postgres=pg_dep)