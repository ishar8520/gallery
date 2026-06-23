import uuid
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from src.api.v1.endpoints.user import patch_user
from src.api.v1.models.user import RequestPatchUser
from src.models.enums import Roles
from src.services import exceptions


@pytest.fixture
def auth():
    return AsyncMock()


@pytest.fixture
def auth_service():
    return AsyncMock()


@pytest.fixture
def user_service():
    return AsyncMock()


@pytest.fixture
def update():
    return RequestPatchUser(username="new_name", email="new@example.com")


class TestPatchUserAuthorization:
    async def test_user_can_update_own_profile(self, auth, auth_service, user_service, update):
        user_id = uuid.uuid4()
        auth.get_jwt_subject.return_value = str(user_id)

        result = await patch_user(
            user_id=user_id,
            user_update=update,
            auth_service=auth_service,
            user_service=user_service,
            auth=auth,
        )

        auth_service.check_role.assert_not_called()
        user_service.patch_user.assert_awaited_once_with(user_id=user_id, user_update=update)
        assert result == {"user": user_id}

    async def test_admin_can_update_other_user(self, auth, auth_service, user_service, update):
        user_id = uuid.uuid4()
        auth.get_jwt_subject.return_value = str(uuid.uuid4())

        await patch_user(
            user_id=user_id,
            user_update=update,
            auth_service=auth_service,
            user_service=user_service,
            auth=auth,
        )

        auth_service.check_role.assert_awaited_once_with(Roles.ADMIN)
        user_service.patch_user.assert_awaited_once_with(user_id=user_id, user_update=update)

    async def test_non_admin_cannot_update_other_user(
        self, auth, auth_service, user_service, update
    ):
        user_id = uuid.uuid4()
        auth.get_jwt_subject.return_value = str(uuid.uuid4())
        auth_service.check_role.side_effect = exceptions.BadPermissionsException

        with pytest.raises(HTTPException) as exc_info:
            await patch_user(
                user_id=user_id,
                user_update=update,
                auth_service=auth_service,
                user_service=user_service,
                auth=auth,
            )

        assert exc_info.value.status_code == 403
        # The write must never happen once authorization fails.
        user_service.patch_user.assert_not_called()
