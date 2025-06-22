from fastapi import APIRouter, Depends, HTTPException, status
from http import HTTPStatus

from src.api.v1.models.auth import (
    ReqRegistration,
    RespRegistration,
    ReqLogin,
    RespLogin
)
# from src.dependences.httpx import get_httpx_client, httpx
from src.services.auth import get_auth_service, AuthService
from src.services.exceptions import (
    BadEmailException,
    EmailExistException,
    UsernameExistException,
    BadCredsException,
    UnauthorizedException
)

router = APIRouter()


@router.post('/registration',
             status_code=status.HTTP_201_CREATED,
             response_model=RespRegistration)
async def register_user(
    request_model: ReqRegistration,
    service: AuthService = Depends(get_auth_service)
):
    try:
        user_id = await service.get_register(request_model)
    except BadEmailException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Wrong email')
    except EmailExistException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='User with this email already exists')
    except UsernameExistException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='User with this username already exists')
    return RespRegistration(id=user_id)


@router.post('/login',
            status_code=status.HTTP_200_OK,
            response_model=RespLogin)
async def login(
    request_model: ReqLogin,
    service: AuthService = Depends(get_auth_service)
):
    try:
        access_token = await service.get_login(request_model)
    except BadCredsException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Wrong username or password'
        )
    return RespLogin(access_token=access_token)


@router.post('/logout',
             status_code=status.HTTP_200_OK,
             response_model=dict)
async def logout(
    service: AuthService = Depends(get_auth_service)
):
    try:
        await service.get_logout()
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authorized')
    return {'logout': 'ok'}


@router.get('/user',
            status_code=status.HTTP_200_OK,
            response_model=dict)
async def user(service: AuthService = Depends(get_auth_service)):
    try:
        user_data = await service.get_user()
    except UnauthorizedException:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authorized')
    return user_data


@router.get('/check',
            status_code=status.HTTP_200_OK,
            response_model=dict)
async def check(
    service: AuthService = Depends(get_auth_service)
):
    try:
        token = await service.check()
    except UnauthorizedException:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authorized')
    return token


@router.post('/test',
             status_code=status.HTTP_201_CREATED,
             response_model=dict)
async def test(
    service: AuthService = Depends(get_auth_service)
):
    token = await service.test()
    return token