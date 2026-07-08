from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from src.services import exceptions
from src.services.user import UserService, get_user_service

router = APIRouter()


@router.get(
    '/confirm',
    status_code=status.HTTP_200_OK,
    response_model=dict,
    description='Подтверждение email-адреса по токену из письма',
)
async def confirm_registration(
    token: str,
    service: Annotated[UserService, Depends(get_user_service)],
):
    try:
        user_id = await service.confirm_registration(token)
    except exceptions.ConfirmationTokenExpiredException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Confirmation token is invalid or expired',
        )
    return {'user_id': user_id}
