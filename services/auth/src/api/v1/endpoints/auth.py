from fastapi import APIRouter, Depends, HTTPException, status
from async_fastapi_jwt_auth import AuthJWT
from http import HTTPStatus

from src.api.v1.models.auth import ReqRegistration, RespRegistration
# from src.dependences.httpx import get_httpx_client, httpx
from src.services.auth import get_auth_service, AuthService
from src.services.exceptions import BadEmailException, EmailExistException, UsernameExistException

router = APIRouter()


@router.post('/registration',
             status_code=HTTPStatus.CREATED,
             response_model=RespRegistration)
async def register_user(
    request_model: ReqRegistration,
    # httpx_client: httpx.AsyncClient = Depends(get_httpx_client),
    service: AuthService = Depends(get_auth_service)
):
    try:
        access_token, refresh_token = await service.get_register(request_model)
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
    return RespRegistration(access_token=access_token,
                            refresh_token=refresh_token)


@router.post('/test',
             status_code=HTTPStatus.CREATED,
             response_model=dict)
async def test(
    service: AuthService = Depends(get_auth_service)
):
    token = await service.test()
    return token