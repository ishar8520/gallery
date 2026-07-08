from unittest.mock import AsyncMock, patch

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


class TestResolveLink:
    def test_redirects_to_stored_url(self, client, redis_mock):
        redis_mock.get = AsyncMock(return_value='http://example.com/target')
        resp = client.get('/s/abc12345', follow_redirects=False)
        assert resp.status_code == 302
        assert resp.headers['location'] == 'http://example.com/target'

    def test_returns_404_for_unknown_token(self, client, redis_mock):
        redis_mock.get = AsyncMock(return_value=None)
        resp = client.get('/s/nonexistent', follow_redirects=False)
        assert resp.status_code == 404
