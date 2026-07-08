import json
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from src.db.redis import get_redis
from src.main import app


@pytest.fixture
def redis_mock():
    return AsyncMock()


@pytest.fixture
def client(redis_mock):
    app.dependency_overrides[get_redis] = lambda: redis_mock
    yield TestClient(app, raise_server_exceptions=False)
    app.dependency_overrides.clear()


class TestCreateLink:
    def test_returns_short_url(self, client, redis_mock):
        redis_mock.set = AsyncMock()
        resp = client.post(
            '/link/api/v1/links',
            json={'url': 'http://example.com/very/long/path', 'ttl': 3600},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert 'short_url' in data
        assert 'token' in data
        assert data['short_url'].endswith(f"/s/{data['token']}")
        redis_mock.set.assert_awaited_once()

    def test_default_ttl_is_used(self, client, redis_mock):
        redis_mock.set = AsyncMock()
        resp = client.post('/link/api/v1/links', json={'url': 'http://example.com'})
        assert resp.status_code == 201
        call_kwargs = redis_mock.set.call_args
        assert call_kwargs.kwargs.get('ex') == 86400

    def test_stores_confirm_token_when_provided(self, client, redis_mock):
        redis_mock.set = AsyncMock()
        resp = client.post(
            '/link/api/v1/links',
            json={'url': '/auth/api/v1/confirm', 'confirm_token': 'uuid-123', 'ttl': 3600},
        )
        assert resp.status_code == 201
        stored_value = json.loads(redis_mock.set.call_args.args[1])
        assert stored_value['confirm_token'] == 'uuid-123'
        assert stored_value['url'] == '/auth/api/v1/confirm'


class TestResolveLink:
    def test_redirects_to_stored_url(self, client, redis_mock):
        stored = json.dumps({'url': 'http://example.com/target', 'confirm_token': None})
        redis_mock.get = AsyncMock(return_value=stored)
        resp = client.get('/s/abc12345', follow_redirects=False)
        assert resp.status_code == 302
        assert resp.headers['location'] == 'http://example.com/target'

    def test_returns_404_for_unknown_token(self, client, redis_mock):
        redis_mock.get = AsyncMock(return_value=None)
        resp = client.get('/s/nonexistent', follow_redirects=False)
        assert resp.status_code == 404

    def test_returns_html_form_when_confirm_token_present(self, client, redis_mock):
        stored = json.dumps({
            'url': 'http://auth/auth/api/v1/confirm',
            'confirm_token': 'secret-uuid',
        })
        redis_mock.get = AsyncMock(return_value=stored)
        resp = client.get('/s/abc12345', follow_redirects=False)
        assert resp.status_code == 200
        assert 'text/html' in resp.headers['content-type']
        assert 'secret-uuid' in resp.text
        assert 'method="POST"' in resp.text
        assert 'http://auth/auth/api/v1/confirm' in resp.text
