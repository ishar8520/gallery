import logging
import re
import secrets
import uuid
from dataclasses import dataclass
from typing import Annotated
from urllib.parse import urlencode

import httpx
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.dependences.postgres import PostgresDep, get_async_postgres
from src.dependences.redis import RedisDep, get_async_redis
from src.models.enums import Roles
from src.models.user import OAuthAccount, User, UserRoles
from src.services import exceptions

logger = logging.getLogger(__name__)

GOOGLE_AUTH_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
GOOGLE_TOKEN_URL = 'https://oauth2.googleapis.com/token'
GOOGLE_USERINFO_URL = 'https://www.googleapis.com/oauth2/v3/userinfo'
OAUTH_STATE_TTL = 600  # 10 минут


@dataclass
class OAuthUserInfo:
    id: uuid.UUID
    username: str
    email: str


class OAuthService:
    def __init__(self, postgres: PostgresDep, redis: RedisDep) -> None:
        self.pg = postgres
        self.redis = redis

    # ── Google: шаг 1 ────────────────────────────────────────────────────────

    async def get_google_auth_url(self) -> str:
        state = secrets.token_urlsafe(32)
        await self.redis.set_value(f'oauth:state:{state}', '1', OAUTH_STATE_TTL)
        params = urlencode({
            'client_id': settings.google.client_id,
            'redirect_uri': settings.google.redirect_uri,
            'response_type': 'code',
            'scope': 'openid email profile',
            'state': state,
            'access_type': 'offline',
            'prompt': 'select_account',
        })
        return f'{GOOGLE_AUTH_URL}?{params}'

    # ── Google: шаг 2 ────────────────────────────────────────────────────────

    async def handle_google_callback(self, code: str, state: str) -> OAuthUserInfo:
        stored = await self.redis.get_value(f'oauth:state:{state}')
        if stored is None:
            raise exceptions.BadCredsException
        await self.redis.drop_value(f'oauth:state:{state}')

        userinfo = await self._exchange_code(code)
        return await self._find_or_create_user(
            provider='google',
            provider_user_id=userinfo['sub'],
            email=userinfo['email'],
            name=userinfo.get('name', ''),
        )

    async def _exchange_code(self, code: str) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.post(GOOGLE_TOKEN_URL, data={
                'code': code,
                'client_id': settings.google.client_id,
                'client_secret': settings.google.client_secret,
                'redirect_uri': settings.google.redirect_uri,
                'grant_type': 'authorization_code',
            })
            resp.raise_for_status()
            token_data = resp.json()

            resp = await client.get(
                GOOGLE_USERINFO_URL,
                headers={'Authorization': f'Bearer {token_data["access_token"]}'},
            )
            resp.raise_for_status()
            return resp.json()

    async def _find_or_create_user(
        self, provider: str, provider_user_id: str, email: str, name: str
    ) -> OAuthUserInfo:
        # 1. Ищем существующий OAuth-аккаунт — возвращаем сразу
        account = await self.pg.get_oauth_account(provider, provider_user_id)
        if account:
            # Извлекаем UUID из account до любых коммитов чтобы не словить expired state
            user_id = account.user_id
            user = await self.pg.get_user_by_id(user_id)
            if user:
                return OAuthUserInfo(id=user.id, username=user.username, email=user.email)

        # 2. Ищем пользователя с таким email — привязываем OAuth-аккаунт
        user = await self.pg.get_user_by_email(email)
        if user:
            # Извлекаем значения ДО commit в add_oauth_account, который экспирирует user
            info = OAuthUserInfo(id=user.id, username=user.username, email=user.email)
            await self.pg.add_oauth_account(OAuthAccount(
                user_id=info.id,
                provider=provider,
                provider_user_id=provider_user_id,
            ))
            return info

        # 3. Создаём нового пользователя
        username = await self._unique_username(name or email.split('@')[0])
        role = await self.pg.get_role(Roles.USER)
        new_user = User(username=username, password=None, email=email)
        user_id = await self.pg.add_user(new_user)
        # После add_user (commit + refresh) user.id доступен, но следующие коммиты
        # экспирируют объект — поэтому сразу фиксируем значения в датакласс
        info = OAuthUserInfo(id=user_id, username=username, email=email)
        await self.pg.add_user_role(UserRoles(user_id=user_id, role=role))
        await self.pg.add_oauth_account(OAuthAccount(
            user_id=user_id,
            provider=provider,
            provider_user_id=provider_user_id,
        ))
        return info

    async def _unique_username(self, base: str) -> str:
        slug = re.sub(r'[^a-zA-Z0-9_]', '_', base)[:20].strip('_') or 'user'
        candidate = slug
        while await self.pg.get_user_by_username(candidate):
            candidate = f'{slug}_{secrets.token_hex(3)}'
        return candidate


def get_oauth_service(
    pg: Annotated[AsyncSession, Depends(get_async_postgres)],
    redis: Annotated[RedisDep, Depends(get_async_redis)],
) -> OAuthService:
    return OAuthService(postgres=pg, redis=redis)
