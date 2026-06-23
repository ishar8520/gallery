import uuid
from unittest.mock import AsyncMock

import pytest

from src.models.enums import Roles
from src.models.user import Role, User
from src.services import exceptions
from src.services.role import RoleService


@pytest.fixture
def pg_session():
    return AsyncMock()


@pytest.fixture
def service(pg_session):
    return RoleService(postgres=pg_session)


class TestAddUserRole:
    async def test_user_not_found(self, service, pg_session):
        pg_session.get_user_by_id.return_value = None
        with pytest.raises(exceptions.UserNotFoundException):
            await service.add_user_role(uuid.uuid4(), Roles.ADMIN)

    async def test_role_already_exists(self, service, pg_session):
        pg_session.get_user_by_id.return_value = User(username="alice")
        pg_session.get_user_roles.return_value = [Roles.ADMIN]
        with pytest.raises(exceptions.RoleExistException):
            await service.add_user_role(uuid.uuid4(), Roles.ADMIN)

    async def test_success_does_not_resave_user(self, service, pg_session):
        pg_session.get_user_by_id.return_value = User(username="alice")
        pg_session.get_user_roles.return_value = []
        pg_session.get_role.return_value = Role(role=Roles.ADMIN)

        await service.add_user_role(uuid.uuid4(), Roles.ADMIN)

        pg_session.add_user_role.assert_awaited_once()
        # Regression: previously add_user_role() called pg_session.add_user()
        # on an unmodified user object before persisting the new role.
        pg_session.add_user.assert_not_called()


class TestDeleteUserRole:
    async def test_user_not_found(self, service, pg_session):
        pg_session.get_user_by_id.return_value = None
        with pytest.raises(exceptions.UserNotFoundException):
            await service.delete_user_role(uuid.uuid4(), Roles.ADMIN)

    async def test_role_not_found(self, service, pg_session):
        pg_session.get_user_by_id.return_value = User(username="alice")
        pg_session.get_user_roles.return_value = []
        with pytest.raises(exceptions.RoleNotFoundException):
            await service.delete_user_role(uuid.uuid4(), Roles.ADMIN)

    async def test_success(self, service, pg_session):
        pg_session.get_user_by_id.return_value = User(username="alice")
        pg_session.get_user_roles.return_value = [Roles.ADMIN]
        pg_session.get_role.return_value = Role(role=Roles.ADMIN)

        await service.delete_user_role(uuid.uuid4(), Roles.ADMIN)

        pg_session.delete_user_role.assert_awaited_once()
