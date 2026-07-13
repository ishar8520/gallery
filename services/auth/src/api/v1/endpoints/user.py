import uuid
from typing import Annotated

from async_fastapi_jwt_auth.exceptions import InvalidHeaderError, JWTDecodeError, MissingTokenError
from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.api.v1.models.user import (
    RequestChangePassword,
    RequestPatchUser,
    ResponseUser,
    ResponseUsersPage,
)
from src.models.enums import Roles
from src.services import exceptions
from src.services.auth import AuthJWT, AuthService, auth_jwt_dep, get_auth_service
from src.services.user import UserService, get_user_service

router = APIRouter()


@router.get(
    '/users',
    status_code=status.HTTP_200_OK,
    response_model=ResponseUsersPage,
    description="""Получить список всех пользователей\n
    Разрешения: Только аутентифицированные пользователи с правами ADMIN"""
)
async def list_users(
    service: Annotated[UserService, Depends(get_user_service)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    auth: Annotated[AuthJWT, Depends(auth_jwt_dep)],
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    try:
        await auth.jwt_required()
        await auth_service.check_role(Roles.ADMIN)
        result = await service.get_all_users(page=page, size=size)
    except exceptions.BadPermissionsException:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail='Current user does not have ADMIN role')
    except (JWTDecodeError, InvalidHeaderError, MissingTokenError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Not authorized')
    return result


@router.post(
    '/user/{user_id}/password',
    status_code=status.HTTP_200_OK,
    response_model=dict,
    description="""Сменить пароль пользователя\n
    Разрешения: Только свой аккаунт"""
)
async def change_password(
    user_id: uuid.UUID,
    request: RequestChangePassword,
    user_service: Annotated[UserService, Depends(get_user_service)],
    auth: Annotated[AuthJWT, Depends(auth_jwt_dep)],
):
    try:
        await auth.jwt_required()
        current_user_id = await auth.get_jwt_subject()
        if current_user_id != str(user_id):
            raise exceptions.BadPermissionsException
        await user_service.change_password(user_id, request)
    except exceptions.UserNotFoundException:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='User not found')
    except exceptions.BadCredsException:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='Current password is incorrect')
    except exceptions.BadPermissionsException:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail='You can only change your own password')
    except (JWTDecodeError, InvalidHeaderError, MissingTokenError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Not authorized')
    return {'user_id': user_id}


@router.get(
    '/user/{user_id}',
    status_code=status.HTTP_200_OK,
    response_model=ResponseUser,
    description="""Получить информацию о пользователе из БД\n
    Разрешения: Только аутентифицированные пользователи"""
)
async def get_user(
    user_id: uuid.UUID,
    service: Annotated[UserService, Depends(get_user_service)],
    auth: Annotated[AuthJWT, Depends(auth_jwt_dep)]
):
    try:
        await auth.jwt_required()
        user = await service.get_user(user_id=user_id)
    except exceptions.UserNotFoundException:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='User not found')
    except (JWTDecodeError, InvalidHeaderError, MissingTokenError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Not authorized')
    return user


@router.delete(
    '/user/{user_id}',
    status_code=status.HTTP_200_OK,
    response_model=dict,
    description="""Удалить пользователя из БД\n
    Разрешения: Только аутентифицированные пользователи с правами ADMIN"""
)
async def delete_user(
    user_id: uuid.UUID,
    user_service: Annotated[UserService, Depends(get_user_service)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    auth: Annotated[AuthJWT, Depends(auth_jwt_dep)]
):
    try:
        await auth.jwt_required()
        await auth_service.check_role(Roles.ADMIN)
        await user_service.delete_user(user_id)
    except exceptions.UserNotFoundException:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='User not found')
    except exceptions.BadPermissionsException:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail='Current user does not have ADMIN role')
    except (JWTDecodeError, InvalidHeaderError, MissingTokenError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Not authorized')
    return {'user_id': user_id}


@router.patch(
    '/user/{user_id}',
    status_code=status.HTTP_200_OK,
    response_model=dict,
    description="""Обновить информацию о пользователе в БД\n
    Разрешения: Только аутентифицированные пользователи с правами ADMIN для редактирования\n
    всех пользователей. Только авторизованные пользователи для редактирования своих данных"""
)
async def patch_user(
    user_id: uuid.UUID,
    user_update: RequestPatchUser,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    user_service: Annotated[UserService, Depends(get_user_service)],
    auth: Annotated[AuthJWT, Depends(auth_jwt_dep)],
):
    try:
        await auth.jwt_required()
        current_user_id = await auth.get_jwt_subject()
        if current_user_id != str(user_id):
            await auth_service.check_role(Roles.ADMIN)
        await user_service.patch_user(user_id=user_id, user_update=user_update)
        await auth_service.get_refresh()
    except exceptions.UserNotFoundException:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='User not found')
    except exceptions.UsernameExistException:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='User with this username already exist')
    except exceptions.EmailExistException:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='User with this email already exist')
    except exceptions.BadPermissionsException:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail='Current user does not have ADMIN role')
    except (JWTDecodeError, InvalidHeaderError, MissingTokenError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Not authorized')
    return {'user': user_id}
