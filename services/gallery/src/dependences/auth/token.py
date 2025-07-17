from typing import Annotated

from fastapi import Depends, Request

async def get_token(request: Request) -> str:
    token = request.headers.get('Authorization', '')
    return token

TokenDep = Annotated[str, Depends(get_token)]
