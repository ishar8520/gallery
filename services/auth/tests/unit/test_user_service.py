import json
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
def redis_mock():
    return AsyncMock()


@pytest.fixture
def kafka_mock():
    return AsyncMock()


@pytest.fixture
def service(pg_session, redis_mock, kafka_mock):
    return UserService(postgres=pg_session, redis=redis_mock, kafka_producer=kafka_mock)


class TestIsValidEmail:
    def test_valid_email(self, service):
        assert service.is_valid_email("user@example.com") is True

    def test_invalid_email(self, service):
        assert service.is_valid_email("not-an-email") is False


class TestGetRegister:
    async def test_success_stores_in_redis(self, service, pg_session, redis_mock, kafka_mock):
        pg_session.get_user_by_username.return_value = None
        pg_session.get_user_by_email.return_value = None
        # set_nx returns True (success) for both username and email
        redis_mock.set_nx.return_value = True

        request_model = RequestRegistration(
            username="alice", email="alice@example.com", password="secret123"
        )
        await service.get_register(request_model)

        pg_session.add_user.assert_not_awaited()
        # set_nx × 2 (username + email) + set_value × 1 (pending data)
        assert redis_mock.set_nx.await_count == 2
        assert redis_mock.set_value.await_count == 1
        kafka_mock.send_and_wait.assert_awaited_once()
        event = kafka_mock.send_and_wait.call_args.args[1]
        assert event['event_type'] == 'email_confirmation_requested'
        assert event['payload']['email'] == 'alice@example.com'

    async def test_username_reserved_in_redis(self, service, pg_session, redis_mock):
        pg_session.get_user_by_username.return_value = None
        pg_session.get_user_by_email.return_value = None
        # set_nx returns False → username already reserved
        redis_mock.set_nx.return_value = False

        request_model = RequestRegistration(
            username="alice", email="alice@example.com", password="secret123"
        )
        with pytest.raises(exceptions.UsernameExistException):
            await service.get_register(request_model)

    async def test_username_exists_in_db(self, service, pg_session, redis_mock):
        pg_session.get_user_by_username.return_value = User(username="alice")

        request_model = RequestRegistration(
            username="alice", email="alice@example.com", password="secret123"
        )
        with pytest.raises(exceptions.UsernameExistException):
            await service.get_register(request_model)

    async def test_email_reserved_in_redis(self, service, pg_session, redis_mock):
        pg_session.get_user_by_username.return_value = None
        pg_session.get_user_by_email.return_value = None
        # username reserved OK, email already taken
        redis_mock.set_nx.side_effect = [True, False]

        request_model = RequestRegistration(
            username="alice", email="alice@example.com", password="secret123"
        )
        with pytest.raises(exceptions.EmailExistException):
            await service.get_register(request_model)

    async def test_invalid_email(self, service, pg_session, redis_mock):
        pg_session.get_user_by_username.return_value = None
        redis_mock.get_value.return_value = None

        request_model = RequestRegistration(
            username="alice", email="not-an-email", password="secret123"
        )
        with pytest.raises(exceptions.BadEmailException):
            await service.get_register(request_model)


class TestConfirmRegistration:
    async def test_success_creates_user_in_db(self, service, pg_session, redis_mock):
        token = str(uuid.uuid4())
        pending = json.dumps({
            'username': 'alice',
            'email': 'alice@example.com',
            'password_hash': '$2b$12$hash',
        })
        redis_mock.get_value.return_value = pending
        pg_session.get_role.return_value = Role(role="USER")
        new_id = uuid.uuid4()
        pg_session.add_user.return_value = new_id

        result = await service.confirm_registration(token)

        assert result == new_id
        pg_session.add_user.assert_awaited_once()
        pg_session.add_user_role.assert_awaited_once()
        assert redis_mock.drop_value.await_count == 3

    async def test_invalid_token_raises(self, service, redis_mock):
        redis_mock.get_value.return_value = None
        with pytest.raises(exceptions.ConfirmationTokenExpiredException):
            await service.confirm_registration('nonexistent-token')


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


class TestForgotPassword:
    async def test_sends_kafka_event_when_user_exists(
        self, service, pg_session, redis_mock, kafka_mock
    ):
        user_id = uuid.uuid4()
        pg_session.get_user_by_email.return_value = User(
            id=user_id, username='alice', email='alice@example.com'
        )
        await service.forgot_password('alice@example.com')

        redis_mock.set_value.assert_awaited_once()
        key = redis_mock.set_value.call_args.args[0]
        assert key.startswith('reset:')
        kafka_mock.send_and_wait.assert_awaited_once()
        event = kafka_mock.send_and_wait.call_args.args[1]
        assert event['event_type'] == 'password_reset_requested'
        assert event['payload']['email'] == 'alice@example.com'

    async def test_silent_when_user_not_found(self, service, pg_session, redis_mock, kafka_mock):
        pg_session.get_user_by_email.return_value = None
        await service.forgot_password('nobody@example.com')
        redis_mock.set_value.assert_not_awaited()
        kafka_mock.send_and_wait.assert_not_awaited()


class TestResetPassword:
    async def test_success_updates_password(self, service, pg_session, redis_mock):
        user_id = uuid.uuid4()
        user = User(id=user_id, username='alice', password='old_hash')
        redis_mock.get_value.return_value = str(user_id)
        pg_session.get_user_by_id.return_value = user

        await service.reset_password('valid-token', 'new_secret')

        pg_session.add_user.assert_awaited_once_with(user)
        assert user.password != 'old_hash'
        redis_mock.drop_value.assert_awaited_once_with('reset:valid-token')

    async def test_expired_token_raises(self, service, redis_mock):
        redis_mock.get_value.return_value = None
        with pytest.raises(exceptions.ResetTokenExpiredException):
            await service.reset_password('bad-token', 'new_secret')

    async def test_user_not_found_raises(self, service, pg_session, redis_mock):
        redis_mock.get_value.return_value = str(uuid.uuid4())
        pg_session.get_user_by_id.return_value = None
        with pytest.raises(exceptions.UserNotFoundException):
            await service.reset_password('token', 'new_secret')
