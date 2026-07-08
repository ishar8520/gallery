import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.security import HTTPBearer

from src.api.v1.endpoints import albums, photos
from src.core.config import settings
from src.dependences.auth.exceptions import UnauthorizedException
from src.kafka.producer import create_producer

logger = logging.getLogger(__name__)

_bearer_scheme = HTTPBearer(auto_error=False)


@asynccontextmanager
async def lifespan(app: FastAPI):
    producer = await create_producer()
    app.state.kafka_producer = producer
    logger.info('Kafka producer started (bootstrap: %s)', settings.kafka.bootstrap_servers)
    yield
    await producer.stop()
    logger.info('Kafka producer stopped')


app = FastAPI(
    title=settings.project.title,
    docs_url='/api/openapi',
    openapi_url='/api/openapi.json',
    dependencies=[Depends(_bearer_scheme)],
    lifespan=lifespan,
)


@app.exception_handler(UnauthorizedException)
async def unauthorized_handler(request: Request, exc: UnauthorizedException):
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authorized')


@app.get('/api/v1/_healthcheck')
async def healthcheck():
    return {}


app.include_router(photos.router, prefix='/api/v1')
app.include_router(albums.router, prefix='/api/v1')
