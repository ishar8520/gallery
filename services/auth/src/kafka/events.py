import uuid
from datetime import UTC, datetime


def user_registered_event(user_id: uuid.UUID, username: str, email: str) -> dict:
    return {
        'event_type': 'user_registered',
        'timestamp': datetime.now(UTC).isoformat(),
        'payload': {
            'user_id': str(user_id),
            'username': username,
            'email': email,
        },
    }
