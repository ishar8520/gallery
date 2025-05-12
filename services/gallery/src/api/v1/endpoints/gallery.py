from fastapi import APIRouter, Depends

from src.api.v1.models.photos import (
    RequestPhotoDownload,
    ResponsePhotoDownload,
    RequestPhotoUpload,
    ResponsePhotoUpload
)
from src.db.minio import MinioClient, get_minio
from src.services.photos import PhotoService, get_photo_service

router = APIRouter()


@router.get(
    '/upload_photo',
    response_model=ResponsePhotoUpload
)
async def upload_photo(request: RequestPhotoUpload) -> ResponsePhotoUpload:
    return {'upload_photo': 'success'}



@router.post(
    '/download_photo',
    response_model=ResponsePhotoDownload
)
async def download_photo(
    request: RequestPhotoDownload,
    service: PhotoService = Depends(get_photo_service),
    database: MinioClient = Depends(get_minio)
    ) -> ResponsePhotoDownload:
    return await service.download_photo_service(request, database)

