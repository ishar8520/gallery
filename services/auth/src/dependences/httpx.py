import httpx
from collections.abc import AsyncGenerator

async def get_httpx_client() -> AsyncGenerator[httpx.AsyncClient]:
    async with httpx.AsyncClient() as client:
        yield client
