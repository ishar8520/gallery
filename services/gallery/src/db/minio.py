from minio import Minio
from minio.error import S3Error

from src.core.config import settings

class MinioClient:
    client: Minio
 
    def __init__(self):
        self.client: Minio = Minio(
            f'{settings.minio.host}:{settings.minio.port}',
            access_key=settings.minio.user,
            secret_key=settings.minio.password,
            secure=False
        )

    async def check_bucket(self, bucket_name: str):
        """Check and create a bucket"""
        print(f'BUCKET_NAME:{bucket_name}')
        if not self.client.bucket_exists(bucket_name):
            self.client.make_bucket(bucket_name)
        return

    async def upload_file(self):
        """Upload photo from bucket"""
        pass


    async def download_file(self, 
                            bucket_name: str, 
                            object_name: str, 
                            file_path: str):
        """Download photo to bucket"""
        await self.check_bucket(bucket_name)
        self.client.fput_object(
            bucket_name=bucket_name,
            object_name=object_name,
            file_path=file_path,
            metadata={'Content-Type': 'image/jpeg'}
        )

async def get_minio() -> MinioClient:
    return MinioClient()
