import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, UploadFile

from src.services.photos import PhotoService, _extract_exif_date


class TestExtractExifDate:
    def test_non_jpeg_returns_none(self):
        assert _extract_exif_date(b'\x89PNG', 'image/png') is None

    def test_jpeg_without_exif_returns_none(self):
        # Minimal valid JPEG bytes that have no EXIF
        data = b'\xff\xd8\xff\xe0' + b'\x00' * 100
        result = _extract_exif_date(data, 'image/jpeg')
        assert result is None

    def test_corrupt_data_returns_none(self):
        assert _extract_exif_date(b'not an image', 'image/jpeg') is None


class TestPhotoServiceUpload:
    def _make_service(self, pg_mock, minio_mock):
        return PhotoService(pg=pg_mock, minio=minio_mock)

    def _make_upload_file(
        self, content=b'fake-image', content_type='image/jpeg', filename='photo.jpg'
    ):
        f = MagicMock(spec=UploadFile)
        f.content_type = content_type
        f.filename = filename
        f.read = AsyncMock(return_value=content)
        return f

    async def test_upload_success(self):
        pg = AsyncMock()
        minio = AsyncMock()
        user_id = uuid.uuid4()
        photo_id = uuid.uuid4()

        minio.upload_file.return_value = ('gallery', f'{user_id}/{photo_id}')
        pg.add_photo.return_value = MagicMock(id=photo_id)

        service = self._make_service(pg, minio)
        file = self._make_upload_file()

        with patch('src.services.photos.uuid.uuid4', return_value=photo_id):
            result = await service.upload_photo(file, title='Test', user_id=user_id)

        minio.upload_file.assert_awaited_once()
        pg.add_photo.assert_awaited_once()
        assert result.id == photo_id

    async def test_upload_invalid_mime_raises_400(self):
        service = self._make_service(AsyncMock(), AsyncMock())
        file = self._make_upload_file(content_type='application/pdf')

        with pytest.raises(HTTPException) as exc_info:
            await service.upload_photo(file, title='Test', user_id=uuid.uuid4())
        assert exc_info.value.status_code == 400

    async def test_upload_too_large_raises_413(self):
        service = self._make_service(AsyncMock(), AsyncMock())
        big_data = b'x' * (50 * 1024 * 1024 + 1)
        file = self._make_upload_file(content=big_data)

        with pytest.raises(HTTPException) as exc_info:
            await service.upload_photo(file, title='Test', user_id=uuid.uuid4())
        assert exc_info.value.status_code == 413  # HTTP_413_CONTENT_TOO_LARGE


class TestPhotoServiceUploadWithAlbum:
    async def test_upload_with_missing_album_raises_404(self):
        pg = AsyncMock()
        pg.get_album.return_value = None
        service = PhotoService(pg=pg, minio=AsyncMock())

        f = MagicMock(spec=UploadFile)
        f.content_type = 'image/jpeg'
        f.filename = 'photo.jpg'
        f.read = AsyncMock(return_value=b'fake')

        with pytest.raises(HTTPException) as exc_info:
            await service.upload_photo(f, title='Test', user_id=uuid.uuid4(), album_id=uuid.uuid4())
        assert exc_info.value.status_code == 404
        assert 'Album' in exc_info.value.detail

    async def test_upload_minio_error_raises_502(self):
        from src.db.minio import S3Error

        pg = AsyncMock()
        pg.get_album.return_value = None
        minio = AsyncMock()
        minio.upload_file.side_effect = S3Error('put_object', 'bucket', 'obj', 'err', 'code', None)
        service = PhotoService(pg=pg, minio=minio)

        f = MagicMock(spec=UploadFile)
        f.content_type = 'image/jpeg'
        f.filename = 'photo.jpg'
        f.read = AsyncMock(return_value=b'fake')

        with pytest.raises(HTTPException) as exc_info:
            await service.upload_photo(f, title='Test', user_id=uuid.uuid4())
        assert exc_info.value.status_code == 502


class TestPhotoServiceList:
    async def test_list_photos_delegates_to_pg(self):
        pg = AsyncMock()
        service = PhotoService(pg=pg, minio=AsyncMock())
        user_id = uuid.uuid4()
        pg.get_photos.return_value = []

        result = await service.list_photos(user_id=user_id)

        pg.get_photos.assert_awaited_once()
        assert result == []

    async def test_list_photos_with_album_filter(self):
        pg = AsyncMock()
        service = PhotoService(pg=pg, minio=AsyncMock())
        user_id = uuid.uuid4()
        album_id = uuid.uuid4()
        pg.get_photos.return_value = []

        await service.list_photos(user_id=user_id, album_id=album_id)

        call_kwargs = pg.get_photos.call_args.kwargs
        assert call_kwargs['album_id'] == album_id

    async def test_list_photos_passes_pagination(self):
        pg = AsyncMock()
        pg.get_photos.return_value = []
        service = PhotoService(pg=pg, minio=AsyncMock())

        await service.list_photos(user_id=uuid.uuid4(), limit=10, offset=20)

        call_kwargs = pg.get_photos.call_args.kwargs
        assert call_kwargs['limit'] == 10
        assert call_kwargs['offset'] == 20


class TestPhotoServiceGetUrl:
    async def test_get_url_returns_photo_and_url(self):
        pg = AsyncMock()
        minio = AsyncMock()
        photo = MagicMock(bucket_name='gallery', object_name='u/p')
        pg.get_photo.return_value = photo
        minio.get_presigned_url.return_value = 'http://minio/signed'

        service = PhotoService(pg=pg, minio=minio)
        result_photo, url = await service.get_photo_url(uuid.uuid4(), uuid.uuid4())

        assert result_photo is photo
        assert url == 'http://minio/signed'

    async def test_get_url_not_found_raises_404(self):
        pg = AsyncMock()
        pg.get_photo.return_value = None

        service = PhotoService(pg=pg, minio=AsyncMock())
        with pytest.raises(HTTPException) as exc_info:
            await service.get_photo_url(uuid.uuid4(), uuid.uuid4())
        assert exc_info.value.status_code == 404


class TestPhotoServiceMove:
    async def test_move_to_album_success(self):
        pg = AsyncMock()
        album = MagicMock()
        photo = MagicMock()
        pg.get_album.return_value = album
        pg.update_photo_album.return_value = photo

        service = PhotoService(pg=pg, minio=AsyncMock())
        result = await service.move_photo(uuid.uuid4(), uuid.uuid4(), uuid.uuid4())

        pg.get_album.assert_awaited_once()
        assert result is photo

    async def test_move_to_none_skips_album_check(self):
        pg = AsyncMock()
        photo = MagicMock()
        pg.update_photo_album.return_value = photo

        service = PhotoService(pg=pg, minio=AsyncMock())
        await service.move_photo(uuid.uuid4(), uuid.uuid4(), None)

        pg.get_album.assert_not_awaited()

    async def test_move_with_missing_album_raises_404(self):
        pg = AsyncMock()
        pg.get_album.return_value = None

        service = PhotoService(pg=pg, minio=AsyncMock())
        with pytest.raises(HTTPException) as exc_info:
            await service.move_photo(uuid.uuid4(), uuid.uuid4(), uuid.uuid4())
        assert exc_info.value.status_code == 404
        assert 'Album' in exc_info.value.detail

    async def test_move_photo_not_found_raises_404(self):
        pg = AsyncMock()
        pg.get_album.return_value = MagicMock()
        pg.update_photo_album.return_value = None

        service = PhotoService(pg=pg, minio=AsyncMock())
        with pytest.raises(HTTPException) as exc_info:
            await service.move_photo(uuid.uuid4(), uuid.uuid4(), uuid.uuid4())
        assert exc_info.value.status_code == 404
        assert 'Photo' in exc_info.value.detail


class TestPhotoServiceDelete:
    async def test_delete_success(self):
        pg = AsyncMock()
        minio = AsyncMock()
        photo = MagicMock(bucket_name='gallery', object_name='u/p')
        pg.get_photo.return_value = photo
        pg.delete_photo.return_value = True

        service = PhotoService(pg=pg, minio=minio)
        await service.delete_photo(uuid.uuid4(), uuid.uuid4())

        minio.delete_file.assert_awaited_once_with('gallery', 'u/p')

    async def test_delete_not_found_raises_404(self):
        pg = AsyncMock()
        pg.get_photo.return_value = None

        service = PhotoService(pg=pg, minio=AsyncMock())
        with pytest.raises(HTTPException) as exc_info:
            await service.delete_photo(uuid.uuid4(), uuid.uuid4())
        assert exc_info.value.status_code == 404

    async def test_delete_order_db_before_minio(self):
        """DB удаляется до MinIO — при сбое MinIO запись не теряется."""
        call_order: list[str] = []

        async def record_db(*a, **kw):
            call_order.append('db')
            return True

        async def record_minio(*a, **kw):
            call_order.append('minio')

        pg = AsyncMock()
        minio = AsyncMock()
        photo = MagicMock(bucket_name='gallery', object_name='u/p')
        pg.get_photo.return_value = photo
        pg.delete_photo.side_effect = record_db
        minio.delete_file.side_effect = record_minio

        service = PhotoService(pg=pg, minio=minio)
        await service.delete_photo(uuid.uuid4(), uuid.uuid4())

        assert call_order == ['db', 'minio']
