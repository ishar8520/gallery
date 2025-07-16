from typing import Annotated
from fastapi import APIRouter, Depends, status, HTTPException

from src.dependences.auth import AuthDepends, get_auth_dep
from src.dependences.auth_exceptions import UnauthorizedException

router = APIRouter()

@router.get(
    '/user',
    status_code=status.HTTP_200_OK,
    response_model=dict
)
async def user_page(
    auth_dep: Annotated[AuthDepends, Depends(get_auth_dep)]
):
    try:
        await auth_dep.get_user_page()
    except UnauthorizedException:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authorized')
    # except Exception as error:
    # except HTTPStatusError
    #     raise HTTPException(status_code=)
    return {}