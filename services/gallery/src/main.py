from fastapi import FastAPI, HTTPException, Request, status

from src.api.v1.endpoints import albums, photos
from src.core.config import settings
from src.dependences.auth.exceptions import UnauthorizedException

app = FastAPI(
    title=settings.project.title,
    docs_url='/api/openapi',
    openapi_url='/api/openapi.json',
)


@app.exception_handler(UnauthorizedException)
async def unauthorized_handler(request: Request, exc: UnauthorizedException):
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authorized')


@app.get('/api/v1/_healthcheck')
async def healthcheck():
    return {}


app.include_router(photos.router, prefix='/api/v1')
app.include_router(albums.router, prefix='/api/v1')
