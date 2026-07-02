import uuid
from collections.abc import AsyncGenerator
from enum import StrEnum

from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.core.config import settings
from src.models.album import Album
from src.models.photo import Photo

engine = create_async_engine(settings.postgresql.dsn)
async_session_maker = async_sessionmaker(bind=engine, class_=AsyncSession)


class SortField(StrEnum):
    UPLOADED_AT = 'uploaded_at'
    EXIF_DATE = 'exif_date'
    TITLE = 'title'
    SIZE = 'size_bytes'


class SortOrder(StrEnum):
    ASC = 'asc'
    DESC = 'desc'


class GalleryPostgresDep:
    session: AsyncSession

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # --- Photo operations ---

    async def add_photo(self, photo: Photo) -> Photo:
        try:
            self.session.add(photo)
            await self.session.commit()
            await self.session.refresh(photo)
            return photo
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def get_photo(self, photo_id: uuid.UUID, user_id: uuid.UUID) -> Photo | None:
        stmt = select(Photo).where(Photo.id == photo_id, Photo.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_photos(
        self,
        user_id: uuid.UUID,
        album_id: uuid.UUID | None = None,
        sort_by: SortField = SortField.UPLOADED_AT,
        order: SortOrder = SortOrder.DESC,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Photo]:
        col = getattr(Photo, sort_by.value)
        order_clause = col.desc() if order == SortOrder.DESC else col.asc()
        stmt = select(Photo).where(Photo.user_id == user_id)
        if album_id is not None:
            stmt = stmt.where(Photo.album_id == album_id)
        stmt = stmt.order_by(order_clause).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_photo_album(
        self, photo_id: uuid.UUID, user_id: uuid.UUID, album_id: uuid.UUID | None
    ) -> Photo | None:
        photo = await self.get_photo(photo_id, user_id)
        if photo is None:
            return None
        try:
            photo.album_id = album_id
            await self.session.commit()
            await self.session.refresh(photo)
            return photo
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def delete_photo(self, photo_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        try:
            stmt = delete(Photo).where(Photo.id == photo_id, Photo.user_id == user_id)
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount > 0
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    # --- Album operations ---

    async def add_album(self, album: Album) -> Album:
        try:
            self.session.add(album)
            await self.session.commit()
            await self.session.refresh(album)
            return album
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def get_album(self, album_id: uuid.UUID, user_id: uuid.UUID) -> Album | None:
        stmt = select(Album).where(Album.id == album_id, Album.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_albums(
        self, user_id: uuid.UUID, limit: int = 100, offset: int = 0
    ) -> list[Album]:
        stmt = (
            select(Album)
            .where(Album.user_id == user_id)
            .order_by(Album.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_album_name(
        self, album_id: uuid.UUID, user_id: uuid.UUID, name: str
    ) -> Album | None:
        album = await self.get_album(album_id, user_id)
        if album is None:
            return None
        try:
            album.name = name
            await self.session.commit()
            await self.session.refresh(album)
            return album
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def delete_album(self, album_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        try:
            stmt = delete(Album).where(Album.id == album_id, Album.user_id == user_id)
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount > 0
        except SQLAlchemyError:
            await self.session.rollback()
            raise


async def get_async_postgres() -> AsyncGenerator[GalleryPostgresDep]:
    async with async_session_maker() as session:
        yield GalleryPostgresDep(session)
