from redis.asyncio import Redis, ConnectionPool

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
        
    def drop_value(self, key: str):
        return self.session.delete(key)
    
async def get_async_redis() -> RedisDep:
    return RedisDep()
