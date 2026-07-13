from typing import Annotated

from async_fastapi_jwt_auth import AuthJWT
from async_fastapi_jwt_auth.exceptions import AuthJWTException
from fastapi import APIRouter, Depends, HTTPException, status

from src.api.v1.models.auth import RequestLogin, ResponseLogin, ResponseMe
from src.services import exceptions
from src.services.auth import AuthService, auth_jwt_dep, get_auth_service

router = APIRouter()


@router.post(
    '/login',
    status_code=status.HTTP_200_OK,
    response_model=ResponseLogin,
    description="""Аутентификация пользователя в системе\n
    Разрешения: Только не аутентифицированные пользователи"""
)
async def login(
    request_model: RequestLogin,
    service: Annotated[AuthService, Depends(get_auth_service)],
    auth: Annotated[AuthJWT, Depends(auth_jwt_dep)]
):
    try:
        await auth.jwt_required()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='You are already login. Logout first')
    except AuthJWTException:
        pass
    try:
        token = await service.get_login(request_model)
    except exceptions.BadCredsException:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='Wrong username or password')
    return token


@router.post(
    '/logout',
    status_code=status.HTTP_200_OK,
    response_model=dict,
    description="""Деаутентификация пользователя из системы\n
    Разрешения: Только аутентифицированные пользователи"""
)
async def logout(
    service: Annotated[AuthService, Depends(get_auth_service)],
    auth: Annotated[AuthJWT, Depends(auth_jwt_dep)],
):
    try:
        await auth.jwt_required()
        await service.get_logout()
    except AuthJWTException:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Not authorized')
    return {'logout': 'ok'}


@router.get(
    '/me',
    status_code=status.HTTP_200_OK,
    response_model=ResponseMe,
    description="""Прочитать информацию из JWT\n
    Разрешения: Только аутентифицированные пользователи"""
)
async def me(
    service: Annotated[AuthService, Depends(get_auth_service)],
    auth: Annotated[AuthJWT, Depends(auth_jwt_dep)]
):
    try:
        await auth.jwt_required()
        user_data = await service.get_me()
    except AuthJWTException:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Not authorized')
    return user_data

@router.get(
    '/verify',
    status_code=status.HTTP_200_OK,
    response_model=ResponseMe,
    description="""Проверка токена для межсервисного взаимодействия\n
    Валидирует подпись JWT и проверяет, что токен не был отозван (logout).\n
    Разрешения: Только аутентифицированные пользователи"""
)
async def verify(
    service: Annotated[AuthService, Depends(get_auth_service)],
    auth: Annotated[AuthJWT, Depends(auth_jwt_dep)]
):
    try:
        await auth.jwt_required()
        user_data = await service.verify_token()
    except exceptions.UnauthorizedException:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Token has been revoked')
    except AuthJWTException:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Not authorized')
    return user_data


@router.post(
    '/refresh',
    status_code=status.HTTP_200_OK,
    response_model=dict
)
async def refresh(
    service: Annotated[AuthService, Depends(get_auth_service)],
    auth: Annotated[AuthJWT, Depends(auth_jwt_dep)]
):
    try:
        await auth.jwt_refresh_token_required()
        access_token = await service.get_refresh()
    except (AuthJWTException, exceptions.UserNotFoundException):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Not authorized')
    return {'access_token': access_token}
