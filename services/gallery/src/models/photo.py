import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base


class Photo(Base):
    __tablename__ = 'photos'
    __table_args__ = {'schema': 'gallery'}

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    album_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey('gallery.albums.id', ondelete='SET NULL'), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    object_name: Mapped[str] = mapped_column(String(1024), nullable=False)
    bucket_name: Mapped[str] = mapped_column(String(255), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(128), nullable=False)
    exif_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    album: Mapped['Album | None'] = relationship('Album', back_populates='photos')  # noqa: F821
