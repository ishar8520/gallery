import uuid
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from fastapi import HTTPException

from src.dependences.auth.auth import get_current_user
from src.dependences.auth.exceptions import UnauthorizedException


class TestGetCurrentUser:
    async def test_missing_token_raises_401(self):
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token='', httpx_client=AsyncMock())
        assert exc_info.value.status_code == 401

    async def test_valid_token_returns_user(self):
        user_id = uuid.uuid4()
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            'user_id': str(user_id),
            'username': 'alice',
            'email': 'alice@example.com',
            'roles': ['USER'],
        }
        client = AsyncMock()
        client.get.return_value = mock_response

        user = await get_current_user(token='Bearer token123', httpx_client=client)

        assert user.user_id == user_id
        assert user.username == 'alice'
        assert user.roles == ['USER']

    async def test_auth_service_error_raises_unauthorized(self):
        client = AsyncMock()
        client.get.side_effect = httpx.RequestError('connection refused')

        with pytest.raises(UnauthorizedException):
            await get_current_user(token='Bearer bad', httpx_client=client)

    async def test_http_status_error_raises_unauthorized(self):
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            '401', request=MagicMock(), response=MagicMock()
        )
        client = AsyncMock()
        client.get.return_value = mock_response

        with pytest.raises(UnauthorizedException):
            await get_current_user(token='Bearer expired', httpx_client=client)
