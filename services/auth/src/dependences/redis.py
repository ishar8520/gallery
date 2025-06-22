from redis.asyncio import Redis, ConnectionPool
from collections.abc import AsyncGenerator

from src.core.config import settings

redis_pool = ConnectionPool.from_url(url=settings.redis.url, decode_responses=True)

class RedisDep:
    session: Redis

    def __init__(self):
        try:
            self.session = Redis(connection_pool=redis_pool)
        except Exception:
            raise
    
    def set_value(self, key: str, value: str, expires: int):
        return self.session.set(key, value, expires)
        
async def get_async_redis() -> RedisDep:
    return RedisDep()
        

# async def get_async_redis() -> AsyncGenerator[Redis, None]:
#     async with Redis(connection_pool=redis_pool) as redis_client:
#         try:
#             yield redis_client
#         except Exception:
#             raise
