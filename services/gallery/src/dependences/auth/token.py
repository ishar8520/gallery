from typing import Annotated

from fastapi import Depends, Request


async def get_token(request: Request) -> str:
    return request.headers.get('Authorization', '')


TokenDep = Annotated[str, Depends(get_token)]
