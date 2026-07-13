import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.v1.endpoints import events, stats
from src.clickhouse.client import init_clickhouse
from src.kafka.consumer import run_consumer_forever

logger = logging.getLogger(__name__)

base_url_prefix = '/ugc'


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_clickhouse()
    logger.info('ClickHouse initialized')
    consumer_task = asyncio.create_task(run_consumer_forever())
    logger.info('UGC Kafka consumer task started')
    yield
    consumer_task.cancel()
    try:
        await consumer_task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title='UGC Service',
    description='User Generated Content analytics',
    docs_url=f'{base_url_prefix}/api/openapi',
    openapi_url=f'{base_url_prefix}/api/openapi.json',
    lifespan=lifespan,
)

base_url_prefix_api = f'{base_url_prefix}/api/v1'


@app.get(f'{base_url_prefix_api}/_healthcheck')
async def healthcheck():
    return {}


app.include_router(events.router, prefix=base_url_prefix_api, tags=['events'])
app.include_router(stats.router, prefix=base_url_prefix_api, tags=['stats'])
