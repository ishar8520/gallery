import httpx

async def get_httpx_client():
    async with httpx.AsyncClient() as client:
        yield client
