import uuid
from unittest.mock import AsyncMock

import bcrypt
import pytest

from src.api.v1.models.auth import RequestLogin
from src.models.user import User
from src.services import exceptions
from src.services.auth import AuthService


def hash_password(raw: str) -> str:
    return bcrypt.hashpw(raw.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


@pytest.fixture
def pg_session():
    return AsyncMock()


@pytest.fixture
def redis_session():
    return AsyncMock()


@pytest.fixture
def jwt():
    return AsyncMock()


@pytest.fixture
def service(pg_session, redis_session, jwt):
    return AuthService(postgres=pg_session, redis=redis_session, jwt=jwt)


class TestGetLogin:
    async def test_unknown_username(self, service, pg_session):
        pg_session.get_user_by_username.return_value = None
        request_model = RequestLogin(username="ghost", password="whatever")
        with pytest.raises(exceptions.BadCredsException):
            await service.get_login(request_model)

    async def test_wrong_password(self, service, pg_session):
        pg_session.get_user_by_username.return_value = User(
            id=uuid.uuid4(), username="alice", password=hash_password("correct-pw")
        )
        request_model = RequestLogin(username="alice", password="wrong-pw")
        with pytest.raises(exceptions.BadCredsException):
            await service.get_login(request_model)

    async def test_success(self, service, pg_session, redis_session, jwt):
        user_id = uuid.uuid4()
        pg_session.get_user_by_username.return_value = User(
            id=user_id,
            username="alice",
            email="alice@example.com",
            password=hash_password("correct-pw"),
        )
        pg_session.get_user_roles.return_value = ["USER"]
        jwt.create_access_token.return_value = "access-token"
        jwt.create_refresh_token.return_value = "refresh-token"

        request_model = RequestLogin(username="alice", password="correct-pw")
        result = await service.get_login(request_model)

        assert result.access_token == "access-token"
        assert result.refresh_token == "refresh-token"
        assert redis_session.set_value.await_count == 2


class TestGetLogout:
    async def test_drops_both_tokens(self, service, redis_session, jwt):
        user_id = str(uuid.uuid4())
        jwt.get_raw_jwt.return_value = {"user_id": user_id}

        await service.get_logout()

        redis_session.drop_value.assert_any_await(f"token:access:{user_id}")
        redis_session.drop_value.assert_any_await(f"token:refresh:{user_id}")
        jwt.unset_jwt_cookies.assert_awaited_once()


class TestCheckRole:
    async def test_pass_when_role_present(self, service, jwt):
        jwt.get_raw_jwt.return_value = {
            "username": "alice",
            "email": "alice@example.com",
            "roles": ["ADMIN"],
        }
        jwt.get_jwt_subject.return_value = str(uuid.uuid4())
        assert await service.check_role("ADMIN") is True

    async def test_raises_when_role_missing(self, service, jwt):
        jwt.get_raw_jwt.return_value = {
            "username": "alice",
            "email": "alice@example.com",
            "roles": ["USER"],
        }
        jwt.get_jwt_subject.return_value = str(uuid.uuid4())
        with pytest.raises(exceptions.BadPermissionsException):
            await service.check_role("ADMIN")
