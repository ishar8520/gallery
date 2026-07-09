from datetime import UTC, datetime


def password_reset_requested_event(token: str, username: str, email: str) -> dict:
    return {
        'event_type': 'password_reset_requested',
        'timestamp': datetime.now(UTC).isoformat(),
        'payload': {
            'token': token,
            'username': username,
            'email': email,
        },
    }


def email_confirmation_requested_event(token: str, username: str, email: str) -> dict:
    return {
        'event_type': 'email_confirmation_requested',
        'timestamp': datetime.now(UTC).isoformat(),
        'payload': {
            'token': token,
            'username': username,
            'email': email,
        },
    }
