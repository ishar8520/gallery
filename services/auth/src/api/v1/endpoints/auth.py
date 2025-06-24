from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from http import HTTPStatus
from typing import Annotated

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
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl='v1/login'
)

@router.post('/registration',
             status_code=status.HTTP_201_CREATED,
             response_model=RespRegistration)
async def register_user(
    request_model: ReqRegistration,
    service: Annotated[AuthService, Depends(get_auth_service)]
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
            response_model=dict)
async def login(
    # request_model: ReqLogin,
    request_model: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: Annotated[AuthService, Depends(get_auth_service)]
):
    try:
        access_token = await service.get_login(request_model)
    except BadCredsException:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Wrong username or password'
        )
    # return RespLogin(access_token=access_token)
    return {'access_token': access_token}


@router.post('/logout',
             status_code=status.HTTP_200_OK,
             response_model=dict)
async def logout(
    token: Annotated[str, Depends(oauth2_scheme)],
    service: Annotated[AuthService, Depends(get_auth_service)]
):
    try:
        await service.get_logout(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authorized')
    return {'logout': 'ok'}


@router.get('/user',
            status_code=status.HTTP_200_OK,
            response_model=dict)
async def user(
    service: Annotated[AuthService, Depends(get_auth_service)],
    token: Annotated[str, Depends(oauth2_scheme)]
):
    try:
        user_data = await service.get_user(token)
    except UnauthorizedException:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authorized')
    return user_data


@router.get('/check',
            status_code=status.HTTP_200_OK,
            response_model=dict)
async def check(
    service: Annotated[AuthService, Depends(get_auth_service)]
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
    service: Annotated[AuthService, Depends(get_auth_service)]
):
    token = await service.test()
    return token