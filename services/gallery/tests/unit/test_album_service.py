import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from src.services.albums import AlbumService


class TestCreateAlbum:
    async def test_create_album_success(self):
        pg = AsyncMock()
        user_id = uuid.uuid4()
        album = MagicMock(id=uuid.uuid4(), user_id=user_id)
        album.name = 'Vacation'
        pg.add_album.return_value = album

        service = AlbumService(pg=pg)
        result = await service.create_album(name='Vacation', user_id=user_id)

        pg.add_album.assert_awaited_once()
        assert result.name == 'Vacation'


class TestGetAlbum:
    async def test_get_existing_album(self):
        pg = AsyncMock()
        album = MagicMock()
        pg.get_album.return_value = album

        service = AlbumService(pg=pg)
        result = await service.get_album(uuid.uuid4(), uuid.uuid4())

        assert result is album

    async def test_get_missing_album_raises_404(self):
        pg = AsyncMock()
        pg.get_album.return_value = None

        service = AlbumService(pg=pg)
        with pytest.raises(HTTPException) as exc_info:
            await service.get_album(uuid.uuid4(), uuid.uuid4())
        assert exc_info.value.status_code == 404


class TestRenameAlbum:
    async def test_rename_success(self):
        pg = AsyncMock()
        album = MagicMock()
        album.name = 'New Name'
        pg.update_album_name.return_value = album

        service = AlbumService(pg=pg)
        result = await service.rename_album(uuid.uuid4(), uuid.uuid4(), 'New Name')

        assert result.name == 'New Name'

    async def test_rename_not_found_raises_404(self):
        pg = AsyncMock()
        pg.update_album_name.return_value = None

        service = AlbumService(pg=pg)
        with pytest.raises(HTTPException) as exc_info:
            await service.rename_album(uuid.uuid4(), uuid.uuid4(), 'Name')
        assert exc_info.value.status_code == 404


class TestDeleteAlbum:
    async def test_delete_success(self):
        pg = AsyncMock()
        pg.delete_album.return_value = True

        service = AlbumService(pg=pg)
        await service.delete_album(uuid.uuid4(), uuid.uuid4())
        pg.delete_album.assert_awaited_once()

    async def test_delete_not_found_raises_404(self):
        pg = AsyncMock()
        pg.delete_album.return_value = False

        service = AlbumService(pg=pg)
        with pytest.raises(HTTPException) as exc_info:
            await service.delete_album(uuid.uuid4(), uuid.uuid4())
        assert exc_info.value.status_code == 404
