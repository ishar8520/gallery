from fastapi import APIRouter, Depends, HTTPException, status
from http import HTTPStatus

from src.api.v1.models.auth import ReqRegistration, ResRegistration
from src.dependences.httpx import get_httpx_client, httpx
from src.services.auth import get_auth_service, AuthService
from src.services.exceptions import BadEmailException, EmailExistException, UsernameExistException

router = APIRouter()


@router.post('/register',
             status_code=HTTPStatus.CREATED,
             response_model=ResRegistration)
async def register_user(
    request_model: ReqRegistration,
    httpx_client: httpx.AsyncClient = Depends(get_httpx_client),
    service: AuthService = Depends(get_auth_service)

):
    try:
        created_user = await service.get_register(request_model)
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
    
    return ResRegistration(id=created_user.id)