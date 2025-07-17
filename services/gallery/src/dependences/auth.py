from typing import Annotated
from fastapi import Depends
import httpx
from async_fastapi_jwt_auth import AuthJWT
from async_fastapi_jwt_auth.auth_jwt import AuthJWTBearer

from src.dependences.httpx import get_httpx_client
from src.dependences.auth_exceptions import UnauthorizedException
from src.dependences.token import TokenDep
from src.core.config import settings

auth_jwt_dep = AuthJWTBearer()

class AuthDepends:
    httpx_client: httpx.AsyncClient
    token: TokenDep

    def __init__(self, httpx_client: httpx.AsyncClient, token: TokenDep):
        self.httpx_client = httpx_client
        self.token = token
    
    async def get_user_page(self):
        try:
            response = await self.httpx_client.get(
                url=f'http://{settings.auth.host}:{settings.auth.port}/auth/api/v1/me',
                headers={'accept': 'application/json', 'Authorization': self.token})
        except httpx.HTTPStatusError:
            raise UnauthorizedException()
        return response.json()

def get_auth_dep(
        token: TokenDep,
        httpx_client: Annotated[httpx.AsyncClient, Depends(get_httpx_client)]
    ):
    return AuthDepends(
        httpx_client=httpx_client,
        token=token)
