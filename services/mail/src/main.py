import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.kafka.consumer import start_consumer
from src.services.mail import MailService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    mail_service = MailService()
    task = asyncio.create_task(start_consumer(mail_service))
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title='Mail Service',
    docs_url='/mail/api/openapi',
    openapi_url='/mail/api/openapi.json',
    lifespan=lifespan,
)


@app.get('/mail/api/v1/_healthcheck')
async def healthcheck():
    return {}
