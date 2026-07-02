import asyncio
import io
import uuid
from datetime import timedelta

from minio import Minio
from minio.error import S3Error

from src.core.config import settings


class MinioClient:
    client: Minio

    def __init__(self) -> None:
        self.client = Minio(
            f'{settings.minio.host}:{settings.minio.port}',
            access_key=settings.minio.user,
            secret_key=settings.minio.password,
            secure=False,
        )

    async def ensure_bucket(self, bucket_name: str) -> None:
        exists = await asyncio.to_thread(self.client.bucket_exists, bucket_name)
        if not exists:
            await asyncio.to_thread(self.client.make_bucket, bucket_name)

    async def upload_file(
        self,
        data: bytes,
        mime_type: str,
        user_id: uuid.UUID,
        photo_id: uuid.UUID,
    ) -> tuple[str, str]:
        """Загружает файл в MinIO, возвращает (bucket_name, object_name)."""
        bucket_name = settings.minio.bucket
        object_name = f'{user_id}/{photo_id}'
        await self.ensure_bucket(bucket_name)
        await asyncio.to_thread(
            self.client.put_object,
            bucket_name,
            object_name,
            io.BytesIO(data),
            len(data),
            content_type=mime_type,
        )
        return bucket_name, object_name

    async def get_presigned_url(
        self,
        bucket_name: str,
        object_name: str,
        expires: timedelta = timedelta(hours=1),
    ) -> str:
        """Возвращает presigned URL для скачивания файла."""
        return await asyncio.to_thread(
            self.client.presigned_get_object,
            bucket_name,
            object_name,
            expires=expires,
        )

    async def delete_file(self, bucket_name: str, object_name: str) -> None:
        await asyncio.to_thread(self.client.remove_object, bucket_name, object_name)


async def get_minio() -> MinioClient:
    return MinioClient()


__all__ = ['MinioClient', 'S3Error', 'get_minio']
