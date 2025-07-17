from typing import Annotated
from fastapi import APIRouter, Depends, status, HTTPException

from src.dependences.auth.auth import AuthJWT, auth_jwt_dep, AuthDepends, get_auth_dep
from src.dependences.auth.exceptions import UnauthorizedException

router = APIRouter()

@router.get(
    '/user',
    status_code=status.HTTP_200_OK,
    response_model=dict
)
async def user_page(
    auth_dep: Annotated[AuthDepends, Depends(get_auth_dep)],
    auth: Annotated[AuthJWT, Depends(auth_jwt_dep)]
):
    try:
        response = await auth_dep.get_user_page()
    except UnauthorizedException:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authorized')
    return response
