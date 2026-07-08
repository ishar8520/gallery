from redis.asyncio import ConnectionPool, Redis

from src.core.config import settings

redis_pool = ConnectionPool.from_url(url=settings.redis.url, decode_responses=True)


class RedisDep:
    session: Redis

    def __init__(self):
        try:
            self.session = Redis(connection_pool=redis_pool)
        except Exception:
            raise

    def get_value(self, key: str):
        return self.session.get(key)

    def set_value(self, key: str, value: str, expires: int):
        return self.session.set(key, value, expires)

    def drop_value(self, key: str):
        return self.session.delete(key)

    def set_nx(self, key: str, value: str, expires: int):
        """SET key value EX expires NX — атомарно, только если ключ не существует."""
        return self.session.set(key, value, ex=expires, nx=True)

async def get_async_redis() -> RedisDep:
    return RedisDep()
