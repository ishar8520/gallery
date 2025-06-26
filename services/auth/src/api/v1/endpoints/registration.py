from typing import Annotated
from fastapi import APIRouter, status, Depends, HTTPException
from async_fastapi_jwt_auth import AuthJWT
from async_fastapi_jwt_auth.auth_jwt import AuthJWTBearer

from src.core.config import settings
from src.api.v1.models.registration import (
    ResponseRegistration,
    RequestRegistration
)
from src.services.exceptions import (
    BadEmailException,
    EmailExistException,
    UsernameExistException
)
from src.services.user import get_user_service, UserService

router = APIRouter()

auth_jwt_dep = AuthJWTBearer()

@AuthJWT.load_config
def get_config():
    return settings.jwt


@router.post('/registration',
    status_code=status.HTTP_201_CREATED,
    response_model=ResponseRegistration)
async def register_user(
    request_model: RequestRegistration,
    service: Annotated[UserService, Depends(get_user_service)]
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
    return ResponseRegistration(id=user_id)
