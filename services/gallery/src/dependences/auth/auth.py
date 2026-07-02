import uuid
from typing import Annotated

import httpx
from fastapi import Depends, HTTPException, status

from src.core.config import settings
from src.dependences.auth.exceptions import UnauthorizedException
from src.dependences.auth.token import TokenDep
from src.dependences.httpx import get_httpx_client


class CurrentUser:
    user_id: uuid.UUID
    username: str
    email: str
    roles: list[str]

    def __init__(self, user_id: str, username: str, email: str, roles: list[str]) -> None:
        self.user_id = uuid.UUID(user_id)
        self.username = username
        self.email = email
        self.roles = roles


async def get_current_user(
    token: TokenDep,
    httpx_client: Annotated[httpx.AsyncClient, Depends(get_httpx_client)],
) -> CurrentUser:
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authorized')
    try:
        response = await httpx_client.get(
            url=f'http://{settings.auth.host}:{settings.auth.port}/auth/api/v1/verify',
            headers={'accept': 'application/json', 'Authorization': token},
        )
        response.raise_for_status()
        data = response.json()
        return CurrentUser(
            user_id=data['user_id'],
            username=data['username'],
            email=data['email'],
            roles=data['roles'],
        )
    except (httpx.HTTPStatusError, httpx.RequestError, KeyError) as exc:
        raise UnauthorizedException() from exc


CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]
