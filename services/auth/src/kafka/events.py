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


def new_oauth_login_event(user_id: str, email: str, username: str, provider: str) -> dict:
    return {
        'event_type': 'new_oauth_login',
        'timestamp': datetime.now(UTC).isoformat(),
        'payload': {
            'user_id': user_id,
            'email': email,
            'username': username,
            'provider': provider,
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
