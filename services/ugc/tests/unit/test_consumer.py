from unittest.mock import MagicMock

import pytest

from src.kafka.consumer import _handle


@pytest.fixture
def svc():
    mock = MagicMock()
    return mock


def photo_uploaded_event(user_id='u1', photo_id='p1', title='cat.jpg'):
    return {
        'event_type': 'photo_uploaded',
        'timestamp': '2026-01-01T12:00:00+00:00',
        'payload': {'user_id': user_id, 'photo_id': photo_id, 'title': title},
    }


def photo_deleted_event(user_id='u1', photo_id='p1'):
    return {
        'event_type': 'photo_deleted',
        'timestamp': '2026-01-01T13:00:00+00:00',
        'payload': {'user_id': user_id, 'photo_id': photo_id},
    }


def user_logged_in_event(user_id='u1', provider='password'):
    return {
        'event_type': 'user_logged_in',
        'timestamp': '2026-01-01T14:00:00+00:00',
        'payload': {'user_id': user_id, 'provider': provider},
    }


class TestHandlePhotoUploaded:
    def test_calls_record_photo_event(self, svc):
        _handle(photo_uploaded_event(), svc)
        svc.record_photo_event.assert_called_once_with(
            event_type='photo_uploaded',
            user_id='u1',
            photo_id='p1',
            title='cat.jpg',
            timestamp='2026-01-01T12:00:00+00:00',
        )

    def test_does_not_call_auth_event(self, svc):
        _handle(photo_uploaded_event(), svc)
        svc.record_auth_event.assert_not_called()


class TestHandlePhotoDeleted:
    def test_calls_record_photo_event_with_empty_title(self, svc):
        _handle(photo_deleted_event(), svc)
        svc.record_photo_event.assert_called_once_with(
            event_type='photo_deleted',
            user_id='u1',
            photo_id='p1',
            title='',
            timestamp='2026-01-01T13:00:00+00:00',
        )


class TestHandleUserLoggedIn:
    def test_calls_record_auth_event(self, svc):
        _handle(user_logged_in_event(provider='google'), svc)
        svc.record_auth_event.assert_called_once_with(
            user_id='u1',
            provider='google',
            timestamp='2026-01-01T14:00:00+00:00',
        )

    def test_unknown_provider_falls_back(self, svc):
        event = {'event_type': 'user_logged_in', 'timestamp': 't', 'payload': {'user_id': 'u2'}}
        _handle(event, svc)
        svc.record_auth_event.assert_called_once_with(
            user_id='u2', provider='unknown', timestamp='t'
        )


class TestHandleUnknownEvent:
    def test_ignores_unknown_event_type(self, svc):
        _handle({'event_type': 'something_else', 'timestamp': 't', 'payload': {}}, svc)
        svc.record_photo_event.assert_not_called()
        svc.record_auth_event.assert_not_called()
        svc.record_click_event.assert_not_called()

    def test_ignores_missing_event_type(self, svc):
        _handle({'payload': {}}, svc)
        svc.record_photo_event.assert_not_called()
