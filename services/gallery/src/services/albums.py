import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, status

from src.dependences.postgres import GalleryPostgresDep, get_async_postgres
from src.models.album import Album


class AlbumService:
    pg: GalleryPostgresDep

    def __init__(self, pg: GalleryPostgresDep) -> None:
        self.pg = pg

    async def create_album(self, name: str, user_id: uuid.UUID) -> Album:
        album = Album(user_id=user_id, name=name)
        return await self.pg.add_album(album)

    async def list_albums(
        self, user_id: uuid.UUID, limit: int = 100, offset: int = 0
    ) -> list[Album]:
        return await self.pg.get_albums(user_id, limit=limit, offset=offset)

    async def get_album(self, album_id: uuid.UUID, user_id: uuid.UUID) -> Album:
        album = await self.pg.get_album(album_id, user_id)
        if album is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Album not found')
        return album

    async def rename_album(self, album_id: uuid.UUID, user_id: uuid.UUID, name: str) -> Album:
        album = await self.pg.update_album_name(album_id, user_id, name)
        if album is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Album not found')
        return album

    async def delete_album(self, album_id: uuid.UUID, user_id: uuid.UUID) -> None:
        deleted = await self.pg.delete_album(album_id, user_id)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Album not found')


def get_album_service(
    pg: Annotated[GalleryPostgresDep, Depends(get_async_postgres)],
) -> AlbumService:
    return AlbumService(pg=pg)
