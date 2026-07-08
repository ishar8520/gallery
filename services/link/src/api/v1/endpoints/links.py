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
    token = str(uuid.uuid4())[:8]
    await redis.set(f'link:{token}', body.url, ex=body.ttl)
    short_url = f'{settings.project.public_url}/s/{token}'
    return CreateLinkResponse(token=token, short_url=short_url)
