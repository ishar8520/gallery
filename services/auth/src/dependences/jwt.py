from async_fastapi_jwt_auth import AuthJWT

from src.core.config import settings


@AuthJWT.load_config
def get_config():
    return settings


async def get_async_jwt():
    return AuthJWT()
