from fastapi import HTTPException
from http import HTTPStatus

from src.api.v1.models.photos import (
    RequestPhotoDownload,
    ResponsePhotoDownload,
    RequestPhotoUpload,
    ResponsePhotoUpload
)
from src.db.minio import MinioClient, S3Error

class PhotoService:
    async def download_photo_service(self,
                                     request: RequestPhotoDownload,
                                     database: MinioClient):
        if not request.bucket_name.islower():
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail='Wrong bucket name')
        try:
            status = await database.download_file(
                bucket_name=request.bucket_name,
                object_name=request.object_name,
                file_path=request.file_path
            )
            return ResponsePhotoDownload(status=status)
        except S3Error as error:
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=error)
        except FileNotFoundError as error:
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=str(error))

            
        
async def get_photo_service():
    return PhotoService()