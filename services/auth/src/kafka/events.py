from datetime import UTC, datetime


def user_logged_in_event(user_id: str, provider: str) -> dict:
    return {
        'event_type': 'user_logged_in',
        'timestamp': datetime.now(UTC).isoformat(),
        'payload': {
            'user_id': user_id,
            'provider': provider,
        },
    }


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
