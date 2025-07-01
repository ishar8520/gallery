from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from async_fastapi_jwt_auth import AuthJWT
from async_fastapi_jwt_auth.exceptions import (
    JWTDecodeError,
    MissingTokenError,
    InvalidHeaderError
)

from src.api.v1.models.auth import (
    RequestLogin,
    ResponseLogin,
    ResponseMe
)
from src.services.auth import get_auth_service, auth_jwt_dep, AuthService
from src.services.exceptions import (
    BadCredsException,
)


router = APIRouter()


@router.post('/login',
    status_code=status.HTTP_200_OK,
    response_model=ResponseLogin)
async def login(
    request_model: RequestLogin,
    service: Annotated[AuthService, Depends(get_auth_service)],
):
    try:
        token = await service.get_login(request_model)
    except BadCredsException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Wrong username or password')
    return token


@router.post('/logout',
    status_code=status.HTTP_200_OK,
    response_model=dict)
async def logout(
    service: Annotated[AuthService, Depends(get_auth_service)],
    auth: Annotated[AuthJWT, Depends(auth_jwt_dep)],
):
    try:
        await auth.jwt_required()
        await service.get_logout()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Not authorized')
    return {'logout': 'ok'}


@router.get('/me',
            status_code=status.HTTP_200_OK,
            response_model=ResponseMe)
async def me(
    service: Annotated[AuthService, Depends(get_auth_service)],
    auth: Annotated[AuthJWT, Depends(auth_jwt_dep)]
):
    try:
        await auth.jwt_required()
        user_data = await service.get_me()
    except (JWTDecodeError, InvalidHeaderError, MissingTokenError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Not authorized')
    return user_data
