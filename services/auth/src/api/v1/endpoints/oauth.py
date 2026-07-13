import logging
from typing import Annotated

from async_fastapi_jwt_auth import AuthJWT
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse

from src.core.config import settings
from src.dependences.postgres import PostgresDep, get_async_postgres
from src.dependences.redis import RedisDep, get_async_redis
from src.services import exceptions
from src.services.oauth import OAuthService, get_oauth_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get('/oauth/google/login')
async def google_login(oauth: Annotated[OAuthService, Depends(get_oauth_service)]):
    url = await oauth.get_google_auth_url()
    return RedirectResponse(url)


@router.get('/oauth/google/callback')
async def google_callback(
    code: str,
    state: str,
    oauth: Annotated[OAuthService, Depends(get_oauth_service)],
    auth: Annotated[AuthJWT, Depends(AuthJWT)],
    redis: Annotated[RedisDep, Depends(get_async_redis)],
    pg: Annotated[PostgresDep, Depends(get_async_postgres)],
):
    try:
        user = await oauth.handle_google_callback(code, state)
    except exceptions.BadCredsException:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid OAuth state')
    except Exception:
        logger.exception('Google OAuth callback failed')
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail='Google авторизация недоступна',
        )

    roles = await pg.get_user_roles(user.id)
    claim = {
        'email': user.email,
        'username': user.username,
        'user_id': str(user.id),
        'roles': [r.value if hasattr(r, 'value') else str(r) for r in roles],
    }

    access_token = await auth.create_access_token(subject=str(user.id), user_claims=claim)
    refresh_token = await auth.create_refresh_token(subject=str(user.id))

    await redis.set_value(
        f'token:access:{user.id}', access_token, int(settings.jwt.access_expires_seconds)
    )
    await redis.set_value(
        f'token:refresh:{user.id}', refresh_token, int(settings.jwt.refresh_expires_seconds)
    )

    redirect_url = f'{settings.app.frontend_url}/oauth-callback?access_token={access_token}'
    response = RedirectResponse(redirect_url)
    # set_access_cookies / set_refresh_cookies принимают response параметр —
    # так куки попадают именно на этот RedirectResponse, а не на внутренний объект AuthJWT.
    await auth.set_access_cookies(access_token, response=response)
    await auth.set_refresh_cookies(refresh_token, response=response)
    return response
