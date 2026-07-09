import uuid
from datetime import datetime

from pydantic import BaseModel


class ResponsePhoto(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    album_id: uuid.UUID | None
    title: str
    original_filename: str
    size_bytes: int
    mime_type: str
    exif_date: datetime | None
    uploaded_at: datetime
    url: str | None = None  # presigned URL; заполняется при листинге

    model_config = {'from_attributes': True}


class ResponsePhotoUrl(BaseModel):
    photo: ResponsePhoto
    url: str


class RequestMovePhoto(BaseModel):
    album_id: uuid.UUID | None = None
