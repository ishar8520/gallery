from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload

from sqlalchemy import select, delete
from collections.abc import AsyncGenerator
from hashlib import sha256

from src.core.config import settings
from src.models.user import User, Role, UserRoles
from src.models.enums import Roles

engine = create_async_engine(settings.postgres.url)
async_session_maker = async_sessionmaker(bind=engine, class_=AsyncSession)



class PostgresDep:
    session: AsyncSession
    
    def __init__(self, session):
        try:
            self.session = session
        except Exception:
            raise

    async def add_user(self, user: User):
        try:
            self.session.add(user)
            await self.session.commit()
            return await self.session.refresh(user)
        except SQLAlchemyError:
            return await self.session.rollback()
    
    async def add_role(self, role: Role):
        try:
            self.session.add(role)
            await self.session.commit()
            return await self.session.refresh(role)
        except SQLAlchemyError:
            return await self.session.rollback()

    async def delete_user(self, user_id: str):
        try:
            await self.session.execute(delete(User).where(User.id==user_id))
            return await self.session.commit()
        except SQLAlchemyError:
            return await self.session.rollback() 
    
    # async def patch_user(self, user_id: str, user_update: User):
        
    #     self.session.add(user_update)


    # async def get_user_with_roles(self, user_id: str):
    #     stmt = (
    #         select(User)
    #         .options(selectinload(User.user_roles).selectinload(UserRoles.role))
    #         .where(User.id==user_id)
    #     )
    #     result = await self.session.execute(stmt)
    #     user = result.scalar_one_or_none()
    #     if not user:
    #         return None, None
    #     roles = [ur.role.role.value for ur in user.user_roles]
    #     return user, roles
    
    async def get_user_by_username(self, username: str):
        stmt = (
            select(User)
            .where(User.username==username)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_user_by_id(self, user_id: str):
        stmt = (
            select(User)
            .where(User.id==user_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_user_by_email(self, email: str):
        stmt = (
            select(User)
            .where(User.email==email)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_user_roles(self, user_id: str):
        stmt = (
            select(User)
            .options(selectinload(User.user_roles).selectinload(UserRoles.role))
            .where(User.id==user_id)
        )
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        return [ur.role.role.value for ur in user.user_roles]

    async def get_role(self, role: Roles):
        stmt = (
            select(Role)
            .where(Role.role==role)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
         
          

    # async def check_user(self, username: str, password: str)
    #     user await self.get_user_by_username(username)
    #     if not user: 
    #     result = await self.session.execute(stmt)
    #     user = result.scalar_one_or_none()


async def get_async_postgres() -> AsyncGenerator[PostgresDep]:
    async with async_session_maker() as session:
        yield PostgresDep(session)
