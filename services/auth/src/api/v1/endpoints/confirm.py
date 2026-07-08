from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, status

from src.services import exceptions
from src.services.user import UserService, get_user_service

router = APIRouter()

_NOT_FOUND = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail='Confirmation token is invalid or expired',
)


@router.get(
    '/confirm',
    status_code=status.HTTP_200_OK,
    response_model=dict,
    description='Подтверждение email-адреса по токену (query param — для тестирования)',
)
async def confirm_registration_get(
    token: str,
    service: Annotated[UserService, Depends(get_user_service)],
):
    try:
        user_id = await service.confirm_registration(token)
    except exceptions.ConfirmationTokenExpiredException:
        raise _NOT_FOUND
    return {'user_id': user_id}


@router.post(
    '/confirm',
    status_code=status.HTTP_200_OK,
    response_model=dict,
    description='Подтверждение email-адреса (POST из HTML-формы link-service)',
)
async def confirm_registration_post(
    token: Annotated[str, Form()],
    service: Annotated[UserService, Depends(get_user_service)],
):
    try:
        user_id = await service.confirm_registration(token)
    except exceptions.ConfirmationTokenExpiredException:
        raise _NOT_FOUND
    return {'user_id': user_id}
