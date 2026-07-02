import io
import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError

from src.db.minio import MinioClient, S3Error, get_minio
from src.dependences.postgres import GalleryPostgresDep, SortField, SortOrder, get_async_postgres
from src.models.photo import Photo

ALLOWED_MIME_TYPES = {'image/jpeg', 'image/png', 'image/gif', 'image/webp'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


def _extract_exif_date(data: bytes, mime_type: str) -> datetime | None:
    if mime_type != 'image/jpeg':
        return None
    try:
        img = Image.open(io.BytesIO(data))
        exif = img._getexif()  # type: ignore[attr-defined]
        if exif is None:
            return None
        # Tag 36867 = DateTimeOriginal
        raw = exif.get(36867)
        if raw is None:
            return None
        return datetime.strptime(raw, '%Y:%m:%d %H:%M:%S').replace(tzinfo=UTC)
    except (UnidentifiedImageError, Exception):
        return None


class PhotoService:
    pg: GalleryPostgresDep
    minio: MinioClient

    def __init__(self, pg: GalleryPostgresDep, minio: MinioClient) -> None:
        self.pg = pg
        self.minio = minio

    async def upload_photo(
        self,
        file: UploadFile,
        title: str,
        user_id: uuid.UUID,
        album_id: uuid.UUID | None = None,
    ) -> Photo:
        mime_type = file.content_type or ''
        if mime_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'Unsupported file type: {mime_type}. '
                f'Allowed: {", ".join(ALLOWED_MIME_TYPES)}',
            )

        data = await file.read()
        if len(data) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail='File too large (max 50 MB)',
            )

        if album_id is not None:
            album = await self.pg.get_album(album_id, user_id)
            if album is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail='Album not found',
                )

        photo_id = uuid.uuid4()
        exif_date = _extract_exif_date(data, mime_type)

        try:
            bucket_name, object_name = await self.minio.upload_file(
                data=data,
                mime_type=mime_type,
                user_id=user_id,
                photo_id=photo_id,
            )
        except S3Error as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f'Storage error: {exc}',
            ) from exc

        photo = Photo(
            id=photo_id,
            user_id=user_id,
            album_id=album_id,
            title=title,
            original_filename=file.filename or 'unknown',
            object_name=object_name,
            bucket_name=bucket_name,
            size_bytes=len(data),
            mime_type=mime_type,
            exif_date=exif_date,
        )
        return await self.pg.add_photo(photo)

    async def list_photos(
        self,
        user_id: uuid.UUID,
        album_id: uuid.UUID | None = None,
        sort_by: SortField = SortField.UPLOADED_AT,
        order: SortOrder = SortOrder.DESC,
    ) -> list[Photo]:
        return await self.pg.get_photos(user_id, album_id=album_id, sort_by=sort_by, order=order)

    async def get_photo_url(self, photo_id: uuid.UUID, user_id: uuid.UUID) -> tuple[Photo, str]:
        photo = await self.pg.get_photo(photo_id, user_id)
        if photo is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Photo not found')
        try:
            url = await self.minio.get_presigned_url(photo.bucket_name, photo.object_name)
        except S3Error as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY, detail=f'Storage error: {exc}'
            ) from exc
        return photo, url

    async def move_photo(
        self, photo_id: uuid.UUID, user_id: uuid.UUID, album_id: uuid.UUID | None
    ) -> Photo:
        photo = await self.pg.update_photo_album(photo_id, user_id, album_id)
        if photo is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Photo not found')
        return photo

    async def delete_photo(self, photo_id: uuid.UUID, user_id: uuid.UUID) -> None:
        photo = await self.pg.get_photo(photo_id, user_id)
        if photo is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Photo not found')
        try:
            await self.minio.delete_file(photo.bucket_name, photo.object_name)
        except S3Error as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY, detail=f'Storage error: {exc}'
            ) from exc
        deleted = await self.pg.delete_photo(photo_id, user_id)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Photo not found')


def get_photo_service(
    pg: Annotated[GalleryPostgresDep, Depends(get_async_postgres)],
    minio: Annotated[MinioClient, Depends(get_minio)],
) -> PhotoService:
    return PhotoService(pg=pg, minio=minio)
