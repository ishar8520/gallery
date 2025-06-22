from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select, Select
from collections.abc import AsyncGenerator
from hashlib import sha256

from src.core.config import settings
from src.models.users import User

engine = create_async_engine(settings.postgres.url)
async_session_maker = async_sessionmaker(bind=engine, class_=AsyncSession)



class PostgresDep:
    session: AsyncSession
    
    def __init__(self):
        try:
            self.session = async_session_maker()
        except Exception:
            raise
        
    async def get_one_or_none(self, statement: Select):
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()
    
    async def add(self, model):
        try:
            self.session.add(model)
            await self.session.commit()
            return await self.session.refresh(model)
        except SQLAlchemyError:
            return self.session.rollback()
    
    async def check_user(self, username: str, password: str):
        user = await self.get_one_or_none(select(User).where(User.username==username))
        if not user:
            return None
        password = sha256(password.encode('utf-8')).hexdigest()
        if user.password != password:
            return None
        return user


async def get_async_pg() -> PostgresDep:
    return PostgresDep()

# async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
#     async with async_session_maker() as session:
#         try:
#             yield session
#         except Exception:
#             await session.rollback()
#             raise
