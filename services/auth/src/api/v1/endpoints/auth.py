from fastapi import APIRouter, Depends, HTTPException
from http import HTTPStatus

from src.api.v1.models.auth import ReqRegistration
from src.dependences.httpx import get_httpx_client, httpx
from src.services.auth import get_auth_service, AuthService

router = APIRouter()


@router.post('/register',
             status_code=HTTPStatus.CREATED,
             response_model=dict)
async def register_user(
    request_model: ReqRegistration,
    httpx_client: httpx.AsyncClient = Depends(get_httpx_client),
    service: AuthService = Depends(get_auth_service)

):
    result = await service.get_register(request_model)
    return {'1': '2'}