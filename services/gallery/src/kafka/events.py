import uuid
from datetime import UTC, datetime


def photo_uploaded_event(
    user_id: uuid.UUID,
    photo_id: uuid.UUID,
    title: str,
    size_bytes: int,
    mime_type: str,
) -> dict:
    return {
        'event_type': 'photo_uploaded',
        'timestamp': datetime.now(UTC).isoformat(),
        'payload': {
            'user_id': str(user_id),
            'photo_id': str(photo_id),
            'title': title,
            'size_bytes': size_bytes,
            'mime_type': mime_type,
        },
    }


def photo_deleted_event(user_id: uuid.UUID, photo_id: uuid.UUID) -> dict:
    return {
        'event_type': 'photo_deleted',
        'timestamp': datetime.now(UTC).isoformat(),
        'payload': {
            'user_id': str(user_id),
            'photo_id': str(photo_id),
        },
    }
