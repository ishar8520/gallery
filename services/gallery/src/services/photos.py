import asyncio
import io
import logging
import uuid
from datetime import UTC, datetime
from typing import Annotated

from aiokafka import AIOKafkaProducer
from fastapi import Depends, HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError

from src.db.minio import MinioClient, S3Error, get_minio
from src.dependences.postgres import GalleryPostgresDep, SortField, SortOrder, get_async_postgres
from src.kafka.events import photo_deleted_event, photo_uploaded_event
from src.kafka.producer import get_kafka_producer
from src.api.v1.models.photos import ResponsePhoto
from src.models.photo import Photo

logger = logging.getLogger(__name__)

UGC_TOPIC = 'ugc-events'

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
    kafka: AIOKafkaProducer

    def __init__(self, pg: GalleryPostgresDep, minio: MinioClient, kafka: AIOKafkaProducer) -> None:
        self.pg = pg
        self.minio = minio
        self.kafka = kafka

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
                status_code=413,
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
        saved = await self.pg.add_photo(photo)
        try:
            await self.kafka.send_and_wait(
                UGC_TOPIC,
                photo_uploaded_event(user_id, photo_id, title, len(data), mime_type),
            )
        except Exception:
            logger.exception('Failed to send photo_uploaded event to Kafka')
        return saved

    async def list_photos(
        self,
        user_id: uuid.UUID,
        album_id: uuid.UUID | None = None,
        no_album: bool = False,
        sort_by: SortField = SortField.UPLOADED_AT,
        order: SortOrder = SortOrder.DESC,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ResponsePhoto]:
        photos = await self.pg.get_photos(
            user_id,
            album_id=album_id,
            no_album=no_album,
            sort_by=sort_by,
            order=order,
            limit=limit,
            offset=offset,
        )

        async def _with_url(photo: Photo) -> ResponsePhoto:
            r = ResponsePhoto.model_validate(photo)
            try:
                r.url = await self.minio.get_presigned_url(photo.bucket_name, photo.object_name)
            except S3Error:
                pass
            return r

        return list(await asyncio.gather(*[_with_url(p) for p in photos]))

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
        if album_id is not None:
            album = await self.pg.get_album(album_id, user_id)
            if album is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Album not found')
        photo = await self.pg.update_photo_album(photo_id, user_id, album_id)
        if photo is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Photo not found')
        return photo

    async def delete_photo(self, photo_id: uuid.UUID, user_id: uuid.UUID) -> None:
        photo = await self.pg.get_photo(photo_id, user_id)
        if photo is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Photo not found')
        # DB first: если MinIO упадёт после — запись сохранится, можно повторить.
        # Если сначала удалить из MinIO, а потом упадёт DB — файл потерян безвозвратно.
        deleted = await self.pg.delete_photo(photo_id, user_id)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Photo not found')
        try:
            await self.minio.delete_file(photo.bucket_name, photo.object_name)
        except S3Error as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY, detail=f'Storage error: {exc}'
            ) from exc
        try:
            await self.kafka.send_and_wait(
                UGC_TOPIC,
                photo_deleted_event(user_id, photo.id),
            )
        except Exception:
            logger.exception('Failed to send photo_deleted event to Kafka')


def get_photo_service(
    pg: Annotated[GalleryPostgresDep, Depends(get_async_postgres)],
    minio: Annotated[MinioClient, Depends(get_minio)],
    kafka: Annotated[AIOKafkaProducer, Depends(get_kafka_producer)],
) -> PhotoService:
    return PhotoService(pg=pg, minio=minio, kafka=kafka)
