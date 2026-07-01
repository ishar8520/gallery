from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.v1.models.registration import RequestRegistration
from src.services import exceptions
from src.services.user import UserService, get_user_service

router = APIRouter()


@router.post(
    '/registration',
    status_code=status.HTTP_201_CREATED,
    response_model=dict,
    description="""Зарегистрировать нового пользователя в системе\n
    Разрешения: Все пользователи""")
async def register_user(
    request_model: RequestRegistration,
    service: Annotated[UserService, Depends(get_user_service)]
):
    try:
        user_id = await service.get_register(request_model)
    except exceptions.BadEmailException:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='Wrong email')
    except exceptions.UserExistException:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='User with this username or email already exists')
    return {'user_id': user_id}
