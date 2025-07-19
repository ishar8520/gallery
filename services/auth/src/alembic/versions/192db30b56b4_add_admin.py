"""Add admin

Revision ID: 192db30b56b4
Revises: 462161efa2d8
Create Date: 2025-07-04 12:08:41.508796

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import bcrypt
from datetime import datetime, timezone
import uuid

from src.core.superuser import admin
from src.models.enums import Roles


# revision identifiers, used by Alembic.
revision: str = '192db30b56b4'
down_revision: Union[str, None] = '462161efa2d8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()

    stmt = sa.text("SELECT id FROM auth.roles WHERE role = :role")
    result = bind.execute(
            stmt,
            {"role": Roles.ADMIN}
        ).fetchone()
    role_id = result[0]


    password = admin.password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password, salt)
    user_id = uuid.uuid4()
    stmt = sa.text(f"""
        INSERT INTO auth.users (id, username, password, email, created_at, updated_at)
        VALUES (:id, :username, :password, :email, :created_at, :updated_at)""")

    bind.execute(
        stmt,
        {
            'id': user_id,
            'username': admin.username,
            'password': hashed_password.decode('utf-8'),
            'email': admin.email,
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc)
        }
    )

    stmt = sa.text(f"""
        INSERT INTO auth.users_roles (id, user_id, role_id, created_at, updated_at)
        VALUES (:id, :user_id, :role_id, :created_at, :updated_at)""")
    bind.execute(
        stmt,
        {
            "id": uuid.uuid4(),
            "user_id": user_id,
            "role_id": role_id,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(f"""
               DELETE FROM auth.users WHERE username={admin.username}""")
