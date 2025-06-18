from fastapi import APIRouter, Depends, HTTPException
from http import HTTPStatus

from src.api.v1.models.auth import ReqRegistration, ResRegistration
from src.dependences.httpx import get_httpx_client, httpx
from src.services.auth import get_auth_service, AuthService, AuthException

router = APIRouter()


@router.post('/register',
             status_code=HTTPStatus.CREATED,
             response_model=ResRegistration)
async def register_user(
    request_model: ReqRegistration,
    httpx_client: httpx.AsyncClient = Depends(get_httpx_client),
    service: AuthService = Depends(get_auth_service)

):
    created_user = await service.get_register(request_model)
    return ResRegistration(id=created_user.id)
    