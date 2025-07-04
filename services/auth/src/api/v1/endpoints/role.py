from typing import Annotated
import uuid
from fastapi import APIRouter, Depends, status, HTTPException
from async_fastapi_jwt_auth.exceptions import (
    JWTDecodeError,
    InvalidHeaderError,
    MissingTokenError
)

from src.services.role import RoleService, get_role_service
from src.services.auth import AuthJWT, auth_jwt_dep, AuthService, get_auth_service
from src.services import exceptions
from src.models.enums import Roles


router = APIRouter()


@router.post(
    '/role/{user_id}',
    status_code=status.HTTP_200_OK,
    response_model=dict,
    description="""Добавить роль пользователю\n
    Разрешения: Только аутентифицированные пользователи с правами ADMIN"""
)
async def add_user_role(
    user_id: uuid.UUID,
    role: Roles,
    role_service: Annotated[RoleService, Depends(get_role_service)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    auth: Annotated[AuthJWT, Depends(auth_jwt_dep)]
):
    try:
        await auth.jwt_required()
        # await auth_service.check_role(Roles.ADMIN.value)
        await role_service.add_user_role(user_id, role)
        await auth_service.get_refresh(user_id=user_id)
    except exceptions.UserNotFoundException:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='User not found')
    except exceptions.RoleExistException:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='User already have this role')
    except exceptions.BadPermissionsException:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=f'Current user have not ADMIN role')
    except (JWTDecodeError, InvalidHeaderError, MissingTokenError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Not authorized')
    return {'user': user_id}

@router.get(
    '/role/{user_id}',
    status_code=status.HTTP_200_OK,
    response_model=dict,
    description="""Получить список ролей пользователя\n
    Разрешения: Только аутентифицированные пользователи"""
)
async def get_user_role(
    user_id: uuid.UUID,
    service: Annotated[RoleService, Depends(get_role_service)],
    auth: Annotated[AuthJWT, Depends(auth_jwt_dep)]
):
    try:
        await auth.jwt_required()
        roles = await service.get_user_role(user_id)
    except (JWTDecodeError, InvalidHeaderError, MissingTokenError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Not authorized')
    return {'user_id': user_id,
            'roles': roles}  


@router.delete(
    '/role/{user_id}',
    status_code=status.HTTP_200_OK,
    response_model=dict,
    description="""Удалить роль у пользователя\n
    Разрешения: Только аутентифицированные пользователи с правами ADMIN"""
)
async def delete_user_role(
    user_id: uuid.UUID,
    role: Roles,
    role_service: Annotated[RoleService, Depends(get_role_service)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    auth: Annotated[AuthJWT, Depends(auth_jwt_dep)]
):
    try:
        await auth.jwt_required()
        await auth_service.check_role(Roles.ADMIN.value)
        await role_service.delete_user_role(user_id, role)
        await auth_service.get_refresh(user_id=user_id)
    except exceptions.UserNotFoundException:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='User not found')
    except exceptions.RoleNotFoundException:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="User don't have this role")
    except exceptions.BadPermissionsException:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=f'Current user have not ADMIN role')
    except (JWTDecodeError, InvalidHeaderError, MissingTokenError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Not authorized')
    return {'user': user_id}
