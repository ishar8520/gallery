from typing import Annotated
from fastapi import APIRouter, Depends, status, HTTPException
from async_fastapi_jwt_auth.exceptions import (
    JWTDecodeError,
    InvalidHeaderError,
    MissingTokenError
)
import uuid

from src.services.role import RoleService, get_role_service
from src.services.auth import AuthJWT, auth_jwt_dep

router = APIRouter()


@router.post(
    '/role/{user_id}',
    status_code=status.HTTP_200_OK,
    response_model=dict
)
async def add_user_role(
    user_id: uuid.UUID,
    service: Annotated[RoleService, Depends(get_role_service)],
    auth: Annotated[AuthJWT, Depends(auth_jwt_dep)]
):
    try:
        await auth.jwt_required()
        await service.add_user_role(user_id)
    except (JWTDecodeError, InvalidHeaderError, MissingTokenError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authorized')
    return {'user': user_id}