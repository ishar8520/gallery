import json
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from redis.asyncio import Redis

from src.core.config import settings
from src.db.redis import get_redis

router = APIRouter()


class CreateLinkRequest(BaseModel):
    url: str
    ttl: int = 86400
    # Если задан, GET /s/{token} вернёт HTML-форму с auto-POST на url с token в теле.
    # Нужно для подтверждения email: токен не попадает в URL и access-логи.
    confirm_token: str | None = None


class CreateLinkResponse(BaseModel):
    token: str
    short_url: str


@router.post(
    '/links',
    status_code=status.HTTP_201_CREATED,
    response_model=CreateLinkResponse,
)
async def create_link(
    body: CreateLinkRequest,
    redis: Annotated[Redis, Depends(get_redis)],
):
    short_token = str(uuid.uuid4())[:8]
    value = json.dumps({'url': body.url, 'confirm_token': body.confirm_token})
    await redis.set(f'link:{short_token}', value, ex=body.ttl)
    short_url = f'{settings.project.public_url}/s/{short_token}'
    return CreateLinkResponse(token=short_token, short_url=short_url)
