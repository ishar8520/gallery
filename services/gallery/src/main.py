from fastapi import FastAPI

from src.api.v1.endpoints import gallery

app = FastAPI(
    title='Gallery service',
    description='Service of photo gallery',
    docs_url='/api/openapi',
    openapi_url='/api/openapi.json'
)

@app.get(f'/api/v1/_healthcheck')
async def healthcheck():
    return {}

app.include_router(
    router=gallery.router,
    tags=['Main']
)