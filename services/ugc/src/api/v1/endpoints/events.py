from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel

from src.core.config import settings
from src.services.ugc import UGCService, get_ugc_service

router = APIRouter()


class ClickEventRequest(BaseModel):
    page: str
    element: str


async def _verify_token(authorization: str | None) -> str:
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authorized')
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f'http://{settings.auth.host}:{settings.auth.port}/auth/api/v1/verify',
                headers={'Authorization': authorization},
            )
            resp.raise_for_status()
            return resp.json()['user_id']
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authorized') from exc


@router.post('/events/click', status_code=status.HTTP_204_NO_CONTENT)
async def track_click(
    body: ClickEventRequest,
    authorization: Annotated[str | None, Header()] = None,
    svc: UGCService = Depends(get_ugc_service),
) -> None:
    user_id = await _verify_token(authorization)
    svc.record_click_event(user_id=user_id, page=body.page, element=body.element)
