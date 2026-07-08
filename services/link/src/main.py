from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import RedirectResponse
from redis.asyncio import Redis

from src.api.v1.endpoints.links import router as links_router
from src.db.redis import get_redis

app = FastAPI(
    title='Link Service',
    docs_url='/link/api/openapi',
    openapi_url='/link/api/openapi.json',
)


@app.get('/link/api/v1/_healthcheck')
async def healthcheck():
    return {}


app.include_router(links_router, prefix='/link/api/v1')


@app.get('/s/{token}', include_in_schema=False)
async def resolve_link(
    token: str,
    redis: Annotated[Redis, Depends(get_redis)],
):
    url = await redis.get(f'link:{token}')
    if url is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Link not found')
    return RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)
