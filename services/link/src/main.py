import json
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
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


_CONFIRM_PAGE = """\
<!DOCTYPE html>
<html lang="ru">
<head><meta charset="utf-8"><title>Подтверждение регистрации</title></head>
<body>
  <form method="POST" action="{action}" id="f">
    <input type="hidden" name="token" value="{token}">
    <p>Подтверждение регистрации...</p>
    <noscript><button type="submit">Подтвердить</button></noscript>
  </form>
  <script>document.getElementById('f').submit();</script>
</body>
</html>
"""


@app.get('/s/{short_token}', include_in_schema=False)
async def resolve_link(
    short_token: str,
    redis: Annotated[Redis, Depends(get_redis)],
):
    raw = await redis.get(f'link:{short_token}')
    if raw is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Link not found')

    data = json.loads(raw)
    url = data['url']
    confirm_token = data.get('confirm_token')

    if confirm_token:
        html = _CONFIRM_PAGE.format(action=url, token=confirm_token)
        return HTMLResponse(content=html)

    return RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)
