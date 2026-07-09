from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.v1.models.user import RequestForgotPassword, RequestResetPassword
from src.services import exceptions
from src.services.user import UserService, get_user_service

router = APIRouter()


@router.post(
    '/forgot-password',
    status_code=status.HTTP_200_OK,
    response_model=dict,
    description='Запрос сброса пароля. Письмо отправляется всегда — email не раскрывается.',
)
async def forgot_password(
    request: RequestForgotPassword,
    user_service: Annotated[UserService, Depends(get_user_service)],
):
    await user_service.forgot_password(request.email)
    return {'detail': 'Если аккаунт существует, письмо со ссылкой для сброса пароля отправлено'}


@router.post(
    '/reset-password',
    status_code=status.HTTP_200_OK,
    response_model=dict,
    description='Сброс пароля по токену из письма.',
)
async def reset_password(
    request: RequestResetPassword,
    user_service: Annotated[UserService, Depends(get_user_service)],
):
    try:
        await user_service.reset_password(request.token, request.new_password)
    except exceptions.ResetTokenExpiredException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Ссылка для сброса пароля недействительна или истекла',
        )
    except exceptions.UserNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Пользователь не найден',
        )
    return {'detail': 'Пароль успешно изменён'}
