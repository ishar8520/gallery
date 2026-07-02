import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from src.api.v1.models.albums import RequestCreateAlbum, RequestUpdateAlbum, ResponseAlbum
from src.dependences.auth.auth import CurrentUserDep
from src.services.albums import AlbumService, get_album_service

router = APIRouter(prefix='/albums', tags=['albums'])

AlbumServiceDep = Annotated[AlbumService, Depends(get_album_service)]


@router.post('', status_code=status.HTTP_201_CREATED, response_model=ResponseAlbum)
async def create_album(
    request: RequestCreateAlbum,
    current_user: CurrentUserDep,
    service: AlbumServiceDep,
):
    album = await service.create_album(name=request.name, user_id=current_user.user_id)
    return ResponseAlbum.model_validate(album)


@router.get('', status_code=status.HTTP_200_OK, response_model=list[ResponseAlbum])
async def list_albums(
    current_user: CurrentUserDep,
    service: AlbumServiceDep,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    albums = await service.list_albums(current_user.user_id, limit=limit, offset=offset)
    return [ResponseAlbum.model_validate(a) for a in albums]


@router.get('/{album_id}', status_code=status.HTTP_200_OK, response_model=ResponseAlbum)
async def get_album(
    album_id: uuid.UUID,
    current_user: CurrentUserDep,
    service: AlbumServiceDep,
):
    album = await service.get_album(album_id, current_user.user_id)
    return ResponseAlbum.model_validate(album)


@router.put('/{album_id}', status_code=status.HTTP_200_OK, response_model=ResponseAlbum)
async def rename_album(
    album_id: uuid.UUID,
    request: RequestUpdateAlbum,
    current_user: CurrentUserDep,
    service: AlbumServiceDep,
):
    album = await service.rename_album(album_id, current_user.user_id, request.name)
    return ResponseAlbum.model_validate(album)


@router.delete('/{album_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_album(
    album_id: uuid.UUID,
    current_user: CurrentUserDep,
    service: AlbumServiceDep,
):
    await service.delete_album(album_id, current_user.user_id)
