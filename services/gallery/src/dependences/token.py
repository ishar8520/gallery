from typing import Annotated

from fastapi import Depends, Request
from async_fastapi_jwt_auth import AuthJWT


async def get_token(request: Request) -> str:
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    return token

TokenDep = Annotated[AuthJWT, Depends(get_token)]
