import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Query, UploadFile, status
from pydantic import BeforeValidator

from src.api.v1.models.photos import RequestMovePhoto, ResponsePhoto, ResponsePhotoUrl
from src.dependences.auth.auth import CurrentUserDep
from src.dependences.postgres import SortField, SortOrder
from src.services.photos import PhotoService, get_photo_service


def _empty_to_none(v: object) -> object:
    return None if v == '' else v


NullableUUID = Annotated[uuid.UUID | None, BeforeValidator(_empty_to_none)]

router = APIRouter(prefix='/photos', tags=['photos'])

PhotoServiceDep = Annotated[PhotoService, Depends(get_photo_service)]


@router.post('', status_code=status.HTTP_201_CREATED, response_model=ResponsePhoto)
async def upload_photo(
    file: UploadFile,
    title: Annotated[str, Form(min_length=1, max_length=255)],
    service: PhotoServiceDep,
    current_user: CurrentUserDep,
    album_id: Annotated[NullableUUID, Form()] = None,
):
    photo = await service.upload_photo(
        file=file,
        title=title,
        user_id=current_user.user_id,
        album_id=album_id,
    )
    return ResponsePhoto.model_validate(photo)


@router.get('', status_code=status.HTTP_200_OK, response_model=list[ResponsePhoto])
async def list_photos(
    current_user: CurrentUserDep,
    service: PhotoServiceDep,
    album_id: Annotated[uuid.UUID | None, Query()] = None,
    sort_by: Annotated[SortField, Query()] = SortField.UPLOADED_AT,
    order: Annotated[SortOrder, Query()] = SortOrder.DESC,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    photos = await service.list_photos(
        user_id=current_user.user_id,
        album_id=album_id,
        sort_by=sort_by,
        order=order,
        limit=limit,
        offset=offset,
    )
    return [ResponsePhoto.model_validate(p) for p in photos]


@router.get('/{photo_id}', status_code=status.HTTP_200_OK, response_model=ResponsePhotoUrl)
async def get_photo(
    photo_id: uuid.UUID,
    current_user: CurrentUserDep,
    service: PhotoServiceDep,
):
    photo, url = await service.get_photo_url(photo_id, current_user.user_id)
    return ResponsePhotoUrl(photo=ResponsePhoto.model_validate(photo), url=url)


@router.patch('/{photo_id}/album', status_code=status.HTTP_200_OK, response_model=ResponsePhoto)
async def move_photo(
    photo_id: uuid.UUID,
    request: RequestMovePhoto,
    current_user: CurrentUserDep,
    service: PhotoServiceDep,
):
    photo = await service.move_photo(photo_id, current_user.user_id, request.album_id)
    return ResponsePhoto.model_validate(photo)


@router.delete('/{photo_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_photo(
    photo_id: uuid.UUID,
    current_user: CurrentUserDep,
    service: PhotoServiceDep,
):
    await service.delete_photo(photo_id, current_user.user_id)
