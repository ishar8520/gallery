from redis.asyncio import ConnectionPool, Redis

from src.core.config import settings

_pool = ConnectionPool.from_url(url=settings.redis.url, decode_responses=True)


def get_redis() -> Redis:
    return Redis(connection_pool=_pool)
