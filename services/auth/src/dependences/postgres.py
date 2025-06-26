from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select, delete, Select
from collections.abc import AsyncGenerator
from hashlib import sha256

from src.core.config import settings
from src.models.users import User

engine = create_async_engine(settings.postgres.url)
async_session_maker = async_sessionmaker(bind=engine, class_=AsyncSession)



class PostgresDep:
    session: AsyncSession
    
    def __init__(self, session):
        try:
            self.session = session
        except Exception:
            raise

    async def add_user(self, model):
        try:
            self.session.add(model)
            await self.session.commit()
            return await self.session.refresh(model)
        except SQLAlchemyError:
            return self.session.rollback()
    
    async def delete_user(self, user_id):
        try:
            await self.session.execute(delete(User).where(User.id==user_id))
            return await self.session.commit()
        except SQLAlchemyError:
            self.session.rollback() 



    async def get_one_or_none(self, statement: Select):
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()
    

    async def check_user(self, username: str, password: str):
        user = await self.get_one_or_none(select(User).where(User.username==username))
        if not user:
            return None
        password = sha256(password.encode('utf-8')).hexdigest()
        if user.password != password:
            return None
        return user



async def get_async_postgres() -> AsyncGenerator[PostgresDep]:
    async with async_session_maker() as session:
        yield PostgresDep(session)
