from typing import Annotated
from fastapi import APIRouter, Depends, status, HTTPException
from async_fastapi_jwt_auth.exceptions import (
    AuthJWTException,
    JWTDecodeError,
    MissingTokenError,
    InvalidHeaderError
)

from src.services.auth import auth_jwt_dep, AuthJWT
from src.services.user import get_user_service, UserService

router = APIRouter()

@router.delete(
    '/delete_user/{user_id}',
    status_code=status.HTTP_200_OK,
    response_model=dict)
async def delete_user(
    user_id: str,
    service: Annotated[UserService, Depends(get_user_service)],
    auth: Annotated[AuthJWT, Depends(auth_jwt_dep)]
):
    try:
        await auth.jwt_required()
        await service.get_delete_user(user_id)
    except (JWTDecodeError, InvalidHeaderError, MissingTokenError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authorized')
    return {'user_id': user_id}
