import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.v1.endpoints import auth, confirm, registration, role, user
from src.core.config import settings
from src.kafka.producer import create_producer

logger = logging.getLogger(__name__)

base_url_prefix = '/auth'


@asynccontextmanager
async def lifespan(app: FastAPI):
    producer = await create_producer()
    app.state.kafka_producer = producer
    logger.info('Kafka producer started (bootstrap: %s)', settings.kafka.bootstrap_servers)
    yield
    await producer.stop()
    logger.info('Kafka producer stopped')


app = FastAPI(
    title='Auth service',
    description='Service for user authorization',
    docs_url=f'{base_url_prefix}/api/openapi',
    openapi_url=f'{base_url_prefix}/api/openapi.json',
    lifespan=lifespan,
)

base_url_prefix_api = f'{base_url_prefix}/api/v1'


@app.get(f'{base_url_prefix_api}/_healthcheck')
async def healthcheck():
    return {}


app.include_router(auth.router, prefix=f'{base_url_prefix_api}', tags=['auth'])
app.include_router(registration.router, prefix=f'{base_url_prefix_api}', tags=['user'])
app.include_router(confirm.router, prefix=f'{base_url_prefix_api}', tags=['user'])
app.include_router(user.router, prefix=f'{base_url_prefix_api}', tags=['user'])
app.include_router(role.router, prefix=f'{base_url_prefix_api}', tags=['role'])
