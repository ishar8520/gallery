from typing import Annotated
from fastapi import Depends
import httpx

from src.dependences.httpx import get_httpx_client
from src.dependences.auth_exceptions import UnauthorizedException
from src.core.config import settings

class AuthDepends:
    httpx_client: httpx.AsyncClient

    def __init__(self, httpx_client: httpx.AsyncClient):
        self.httpx_client = httpx_client
    
    async def get_user_page(self):
        try:
            response = await self.httpx_client.get(
                url=f'http://{settings.auth.host}:{settings.auth.port}/auth/api/v1/me')
            
                # cookies=self.get_cookies())
            status = await response.raise_for_status()
        except httpx.HTTPStatusError as err:
            print(err)
            raise UnauthorizedException()
        return response.json()

    # def get_cookies(self):
    #     return {
    #         access_token_cookie
    #     }

def get_auth_dep(
        httpx_client: Annotated[httpx.AsyncClient, Depends(get_httpx_client)]
    ):
    return AuthDepends(
        httpx_client=httpx_client)
