from typing import Annotated
import uuid
from fastapi import APIRouter, Depends, status, HTTPException
from async_fastapi_jwt_auth.exceptions import (
    JWTDecodeError,
    MissingTokenError,
    InvalidHeaderError
)

from src.services.auth import auth_jwt_dep, get_auth_service, AuthJWT, AuthService
from src.services.user import get_user_service, UserService
from src.services import exceptions
from src.models.enums import Roles
from src.api.v1.models.user import ResponseUser, RequestPatchUser

router = APIRouter()


@router.get(
    '/user/{user_id}',
    status_code=status.HTTP_200_OK,
    response_model=ResponseUser
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
    response_model=dict)
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
                            detail=f'Current user have not ADMIN role')
    except (JWTDecodeError, InvalidHeaderError, MissingTokenError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Not authorized')
    return {'user_id': user_id}


@router.patch(
    '/user/{user_id}',
    status_code=status.HTTP_200_OK,
    response_model=dict,
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
        await user_service.patch_user(user_id=user_id, user_update=user_update)
        await auth_service.get_refresh(user_id=user_id)
    except exceptions.UserNotFoundException:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='User not found')
    except exceptions.UsernameExistException:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='User with this username already exist')
    except exceptions.EmailExistException:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='User with this email already exist')
    except (JWTDecodeError, InvalidHeaderError, MissingTokenError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Not authorized')
    return {'user': user_id}
