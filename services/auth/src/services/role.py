from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from src.dependences.postgres import PostgresDep, get_async_postgres
from src.models.enums import Roles
from src.models.user import UserRoles

class RoleService:
    pg_session: PostgresDep

    def __init__(self, postgres):
        self.pg_session=postgres


    async def add_user_role(self, user_id: uuid.UUID, role: Roles):
        role = await self.pg_session.get_role(role)
        user = await self.pg_session.get_user_by_id(user_id)
        user_role = UserRoles(user=user, role=role)
        user_id = await self.pg_session.add_user(user)
        await self.pg_session.add_role(user_role)
        pass


async def get_role_service(
    pg_dep: Annotated[AsyncSession, Depends(get_async_postgres)],
    ) -> RoleService:
    return RoleService(postgres=pg_dep)