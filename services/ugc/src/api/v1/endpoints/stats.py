from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, status

from src.core.config import settings
from src.services.ugc import UGCService, get_ugc_service

router = APIRouter()


async def _require_admin(authorization: str | None) -> None:
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authorized')
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f'http://{settings.auth.host}:{settings.auth.port}/auth/api/v1/verify',
                headers={'Authorization': authorization},
            )
            resp.raise_for_status()
            data = resp.json()
            if 'ADMIN' not in data.get('roles', []):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Admin only')
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authorized') from exc


@router.get('/stats/photos')
async def photo_stats(
    authorization: Annotated[str | None, Header()] = None,
    svc: UGCService = Depends(get_ugc_service),
) -> dict:
    await _require_admin(authorization)
    return svc.get_photo_stats()


@router.get('/stats/auth')
async def auth_stats(
    authorization: Annotated[str | None, Header()] = None,
    svc: UGCService = Depends(get_ugc_service),
) -> dict:
    await _require_admin(authorization)
    return svc.get_auth_stats()


@router.get('/stats/clicks')
async def click_stats(
    authorization: Annotated[str | None, Header()] = None,
    svc: UGCService = Depends(get_ugc_service),
) -> dict:
    await _require_admin(authorization)
    return svc.get_click_stats()
