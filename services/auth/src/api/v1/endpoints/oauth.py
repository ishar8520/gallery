import logging
from typing import Annotated
from urllib.parse import quote

from async_fastapi_jwt_auth import AuthJWT
from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse

from src.core.config import settings
from src.dependences.postgres import PostgresDep, get_async_postgres
from src.dependences.redis import RedisDep, get_async_redis
from src.services import exceptions
from src.services.oauth import OAuthService, OAuthUserInfo, get_oauth_service

logger = logging.getLogger(__name__)
router = APIRouter()


def _error_redirect(message: str) -> RedirectResponse:
    return RedirectResponse(
        f'{settings.app.frontend_url}/oauth-callback?error={quote(message)}'
    )


async def _issue_tokens_and_redirect(
    user: OAuthUserInfo,
    auth: AuthJWT,
    redis: RedisDep,
    pg: PostgresDep,
) -> RedirectResponse:
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
    await auth.set_access_cookies(access_token, response=response)
    await auth.set_refresh_cookies(refresh_token, response=response)
    return response


# ── GitHub ────────────────────────────────────────────────────────────────────

@router.get('/oauth/github/login')
async def github_login(oauth: Annotated[OAuthService, Depends(get_oauth_service)]):
    url = await oauth.get_github_auth_url()
    return RedirectResponse(url)


@router.get('/oauth/github/callback')
async def github_callback(
    code: str,
    state: str,
    oauth: Annotated[OAuthService, Depends(get_oauth_service)],
    auth: Annotated[AuthJWT, Depends(AuthJWT)],
    redis: Annotated[RedisDep, Depends(get_async_redis)],
    pg: Annotated[PostgresDep, Depends(get_async_postgres)],
):
    try:
        user = await oauth.handle_github_callback(code, state)
        return await _issue_tokens_and_redirect(user, auth, redis, pg)
    except exceptions.BadCredsException:
        return _error_redirect('Недействительная ссылка авторизации. Попробуйте снова.')
    except Exception:
        logger.exception('GitHub OAuth callback failed')
        return _error_redirect('GitHub авторизация не удалась. Попробуйте позже.')


# ── Google ────────────────────────────────────────────────────────────────────

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
        return await _issue_tokens_and_redirect(user, auth, redis, pg)
    except exceptions.BadCredsException:
        return _error_redirect('Недействительная ссылка авторизации. Попробуйте снова.')
    except Exception:
        logger.exception('Google OAuth callback failed')
        return _error_redirect('Google авторизация не удалась. Попробуйте позже.')
