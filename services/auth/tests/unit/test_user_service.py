import uuid
from unittest.mock import AsyncMock

import pytest

from src.api.v1.models.registration import RequestRegistration
from src.api.v1.models.user import RequestPatchUser
from src.models.user import Role, User
from src.services import exceptions
from src.services.user import UserService


@pytest.fixture
def pg_session():
    return AsyncMock()


@pytest.fixture
def service(pg_session):
    return UserService(postgres=pg_session)


class TestIsValidEmail:
    def test_valid_email(self, service):
        assert service.is_valid_email("user@example.com") is True

    def test_invalid_email(self, service):
        assert service.is_valid_email("not-an-email") is False


class TestGetRegister:
    async def test_success(self, service, pg_session):
        pg_session.get_user_by_username.return_value = None
        pg_session.get_user_by_email.return_value = None
        pg_session.get_role.return_value = Role(role="USER")
        new_id = uuid.uuid4()
        pg_session.add_user.return_value = new_id

        request_model = RequestRegistration(
            username="alice", email="alice@example.com", password="secret123"
        )
        result = await service.get_register(request_model)

        assert result == new_id
        pg_session.add_user.assert_awaited_once()
        pg_session.add_user_role.assert_awaited_once()

    async def test_username_already_exists(self, service, pg_session):
        pg_session.get_user_by_username.return_value = User(username="alice")

        request_model = RequestRegistration(
            username="alice", email="alice@example.com", password="secret123"
        )
        with pytest.raises(exceptions.UserExistException):
            await service.get_register(request_model)

    async def test_email_already_exists(self, service, pg_session):
        pg_session.get_user_by_username.return_value = None
        pg_session.get_user_by_email.return_value = User(email="alice@example.com")

        request_model = RequestRegistration(
            username="alice", email="alice@example.com", password="secret123"
        )
        with pytest.raises(exceptions.UserExistException):
            await service.get_register(request_model)

    async def test_invalid_email(self, service, pg_session):
        pg_session.get_user_by_username.return_value = None
        pg_session.get_user_by_email.return_value = None

        request_model = RequestRegistration(
            username="alice", email="not-an-email", password="secret123"
        )
        with pytest.raises(exceptions.BadEmailException):
            await service.get_register(request_model)


class TestGetUser:
    async def test_not_found(self, service, pg_session):
        pg_session.get_user_by_id.return_value = None
        with pytest.raises(exceptions.UserNotFoundException):
            await service.get_user(uuid.uuid4())

    async def test_found(self, service, pg_session):
        user_id = uuid.uuid4()
        pg_session.get_user_by_id.return_value = User(
            id=user_id, username="alice", email="alice@example.com"
        )
        result = await service.get_user(user_id)
        assert result.user_id == user_id
        assert result.username == "alice"


class TestPatchUser:
    async def test_updates_changed_fields(self, service, pg_session):
        user = User(username="old_name", email="old@example.com")
        pg_session.get_user_by_id.return_value = user
        pg_session.get_user_by_username.return_value = None
        pg_session.get_user_by_email.return_value = None
        pg_session.add_user.return_value = uuid.uuid4()

        update = RequestPatchUser(username="new_name", email="old@example.com")
        await service.patch_user(user_id=uuid.uuid4(), user_update=update)

        assert user.username == "new_name"
        assert user.email == "old@example.com"
        pg_session.add_user.assert_awaited_once_with(user)

    async def test_username_conflict(self, service, pg_session):
        user = User(username="old_name", email="old@example.com")
        pg_session.get_user_by_id.return_value = user
        pg_session.get_user_by_username.return_value = User(username="taken")

        update = RequestPatchUser(username="taken", email="old@example.com")
        with pytest.raises(exceptions.UsernameExistException):
            await service.patch_user(user_id=uuid.uuid4(), user_update=update)

    async def test_not_found(self, service, pg_session):
        pg_session.get_user_by_id.return_value = None
        update = RequestPatchUser(username="x", email="x@example.com")
        with pytest.raises(exceptions.UserNotFoundException):
            await service.patch_user(user_id=uuid.uuid4(), user_update=update)
